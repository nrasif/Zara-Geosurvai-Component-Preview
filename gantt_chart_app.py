from dash import html, Dash, dcc, Input, Output, State, callback
import dash_ag_grid as dag
import pandas as pd
import plotly.figure_factory as ff
import dash_mantine_components as dmc
import pandas as pd
from datetime import datetime, timedelta
import pytz

from io import StringIO, BytesIO
import base64

import openai_api_key
import openai

import prompt

import chartgpt as cg

from pandasai import SmartDataframe
from pandasai.llm import OpenAI


openai.api_key = openai_api_key.KEY
llm = OpenAI(api_token=openai.api_key)


# databases
# df = pd.read_excel('data/pm_data.xlsx')


# functions and classes
def jumbotron():
    return html.Div(
        html.Div(
            [
                html.H1("Geosurvai", className="app-name"),
                html.P(
                    "Get to know with TrackAI Pro! Project Management is enhanced with the help of Zara Assistant",
                    className="desc-zara-1",
                ),
                html.P("How does it work?", className="desc-zara-1"),
            ],
            className="jumbotron",
        )
    )


def stepper():
    return html.Div(
        [
            dmc.Stepper(
                className="stepper",
                active=0,
                orientation="horizontal",
                children=[
                    dmc.StepperStep(
                        label="First Step", description="Upload your own CSV/Excel"
                    ),
                    dmc.StepperStep(
                        label="Second Step", description="Track your project"
                    ),
                    dmc.StepperStep(label="Final Step", description="Ask Zara!"),
                ],
            )
        ]
    )


def upload_modals():
    return html.Div(
        [
            dcc.Store(
                id="memory-input"
            ),  # For development purposes only (should be Redis or Kafka for production stage)
            dmc.Button(
                "Upload CSV/Excel",
                id="csv-button",
                style={"background-color": "#112D4E", "marginLeft": "75px"},
            ),
            dmc.Modal(
                title="Upload",
                id="upload-modal",
                size="lg",
                zIndex=999,
                children=[
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            ["Drag and Drop or ", html.A("Select Files")]
                        ),
                        style={
                            "width": "100%",
                            "height": "60px",
                            "lineHeight": "60px",
                            "borderWidth": "1px",
                            "borderStyle": "dashed",
                            "borderRadius": "10px",
                            "textAlign": "center",
                            "margin": "20px 0px 20px 0px",
                        },
                        multiple=False,
                    ),
                    html.Div(id="alert-uploaded"),
                    dmc.Space(h=20),
                    dmc.Button(
                        "Close", color="red", variant="outline", id="modal-close-button"
                    ),
                ],
            ),
        ]
    )


# chart
# fig = ff.create_gantt(df, index_col='Resource', show_colorbar=True, group_tasks=True)
# def create_chart(data):
#     fig = ff.create_gantt(data, index_col='Resource', show_colorbar=True, group_tasks=True)
#     return fig

# backends


# for uploading the files
@callback(
    Output("memory-input", "data"),
    Output("alert-uploaded", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def update_output(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    # file_extension = os.path.splitext(filename)[1].lower()

    if "csv" in filename:
        df = pd.read_csv(StringIO(decoded.decode("utf-8")))

    elif "xlsx" in filename:
        df = pd.read_excel(BytesIO(decoded))

    preview = html.Div(
        [
            dmc.Space(h=10),
            dmc.Alert(f'File uploaded : {filename}', title='Your file has successfully uploaded!',id="alert-upload", color='green')
        ]
    )

    return df.to_dict("records"), preview


# closing the modal opened
@callback(
    Output("upload-modal", "opened"),
    Input("csv-button", "n_clicks"),
    Input("modal-close-button", "n_clicks"),
    State("upload-modal", "opened"),
    prevent_initial_call=True,
)
def modal_demo(nc1, nc2, opened):
    return not opened


# df preview
def preview_table():
    return html.Div(
        html.Div(
            [
                # html.H1("Test on preview data table", className="app-name"),
                # dmc.Space(h=10),
                html.P(
                    "Preview Data",
                    className="desc-zara-1",
                    style={"marginLeft":"80px","marginTop":"50px"}
                ),
                html.Div(id='preview-data-table', style={"marginLeft":"80px", "marginRight":"85px", "marginTop":"25px", "marginBottm":"25px"})
            ]
        )
    )
    
@callback(
    Output("preview-data-table", "children"),
    Input("memory-input", "data"),
)
def render(input_data):
    if not input_data:
        df_example = pd.read_excel("data_example/pm_data_example.xlsx")
        
        # Convert datetime columns to desired format
        date_columns = ["Start", "Finish"]
        for col in date_columns:
            df_example[col] = pd.to_datetime(df_example[col], format="%Y-%m-%dT%H:%M:%S").dt.strftime("%d-%m-%Y")
        
        return html.Div(
            [
                # html.H5("File uploaded : " + filename),
                dmc.Space(h=10),
                dag.AgGrid(
                    id="grid-data",
                    rowData=df_example.to_dict("records"),
                    columnDefs=[{"field": i, "editable": True} for i in df_example.columns],
                    defaultColDef={"sortable": True, "resizable": True, "editable": True},
                    style={'height':'630px'}
                    # columnSize="sizeToFit",
                ),
                dmc.Button(
                    "Add Row",
                    id="add-row-button",
                    style={"background-color": "#112D4E", "marginTop": "25px"},
                ),
                # dmc.Button(
                # "Delete Selected Row",
                # id="delete-row-button",
                # style={"background-color": "#112D4E", "marginTop": "25px", "marginLeft": "35px"},
                # ),
                dmc.Button(
                "Export as CSV",
                id="export-csv-button",
                style={"background-color": "#112D4E", "marginTop": "25px", "marginLeft": "35px"},
                ),
                dcc.Store(id="memory-ag-grid-data", data=df_example.to_dict("records")),
            ]
        )

    df = pd.DataFrame(input_data)
    
    # Convert datetime columns to desired format
    date_columns = ["Start", "Finish"]
    for col in date_columns:
        # df[col] = pd.to_datetime(df[col]).dt.strftime("%d/%m/%Y")
        df[col] = pd.to_datetime(df[col], format="%Y-%m-%dT%H:%M:%S").dt.strftime("%d-%m-%Y")
    
    return html.Div(
        [
            # html.H5("File uploaded : " + filename),
            dmc.Space(h=10),
            dag.AgGrid(
                id="grid-data",
                rowData=df.to_dict("records"),
                columnDefs=[{"field": i, "editable": True} for i in df.columns],
                defaultColDef={"sortable": True, "resizable": True, "editable": True},
                style={'height':'630px'},
                # columnSize="sizeToFit",
                csvExportParams={
                    "fileName": "pm_data.csv",
                }
            ),
            dmc.Button(
                "Add Row",
                id="add-row-button",
                style={"background-color": "#112D4E", "marginTop": "25px"},
            ),
            dmc.Button(
                "Export as CSV",
                id="export-csv-button",
                style={"background-color": "#112D4E", "marginTop": "25px", "marginLeft": "35px"},
            ),
            dcc.Store(id="memory-ag-grid-data", data=df.to_dict("records")),
        ]
    )

# adding row to table
@callback(
    Output("grid-data", "rowData"),
    Output("memory-ag-grid-data", "data"),
    Input("add-row-button", "n_clicks"),
    State("memory-ag-grid-data", "data"),
)
def add_row(n_clicks, existing_data):
    if n_clicks:
        new_row = {"Task": "", "Start": "", "Finish": "", "Priority": "", "Status": ""}
        existing_data.append(new_row)
        return existing_data, existing_data
    return existing_data, existing_data

# # adding row to table
# @callback(
#     Output("grid-data", "rowData"),
#     Output("memory-ag-grid-data", "data"),
#     Input("add-row-button", "n_clicks"),
#     Input("delete-row-button", "n_clicks"),
#     State("memory-ag-grid-data", "data"),
#     State("grid-data", "selectedRows"),
# )
# def modify_data(add_clicks, delete_clicks, existing_data, selected_rows):
#     # Get column names from the existing data
#     columns = existing_data[0].keys() if existing_data else None

#     # Add a new row with empty values for each column
#     if add_clicks:
#         new_row = {col: "" for col in columns}
#         existing_data.append(new_row)

#     # Delete selected rows
#     if delete_clicks and selected_rows:
#         # Convert selected rows to a set for efficient removal
#         selected_row_ids = [row["id"] for row in selected_rows]
#         existing_data = [row for row in existing_data if row["id"] not in selected_row_ids]

#     return existing_data, existing_data

# saving the data
@callback(
    Output("grid-data", "exportDataAsCsv"),
    Input("export-csv-button", "n_clicks"),
)
def export_data_as_csv(n_clicks):
    if n_clicks:
        return True
    return False

# setting the filter values
def filter_value():
    index_col_dropdown = dmc.Select(
                label="Select Filter",
                placeholder="Select one",
                id="index-col-dropdown",
                value="Priority",
                data=[
                    {"value": "Priority", "label": "Priority"},
                    {"value": "Status", "label": "Status"},
                    {"value": "Progress", "label": "Progress"},
                ],
                style={"width": 100, 'marginLeft':'80px', 'marginTop':'30px'},
            )
    return html.Div(
        [
            index_col_dropdown
        ]
    )
    
# callback to sychronize filter and gantt chart

# setting the df into gantt chart
def create_chart():
    @callback(
        Output("gantt-chart", "children"),
        Input("memory-input", "data"),
        Input("index-col-dropdown", "value"),
    )
    def render(input_data, selected_index_col):
        # colors = {
        #         "High": "#0DFF02",
        #         "Medium": "#EBD421",
        #         "Low": "#FF0C46",
        # }
                    
            # Dynamically generate colors based on selected index column
        if selected_index_col == "Priority":
            color_scale = {
                "Low": "#5FC605",
                "Medium": "#D5AC04",
                "High": "#A80202"
            }
        elif selected_index_col == "Status":
            color_scale = {
                "Completed": "#0C16DB",
                "In-Progress": "#9B02EA",
                "Queue-Initiation": "#D5D004"
            }
        elif selected_index_col == "Progress":
            # Use "Viridis" color scale based on percentage
            color_scale = "YlGnBu"
        else:
            # Default color scale for other cases
            color_scale = None
                    
        if not input_data:
            df_example = pd.read_excel("data_example/pm_data_example.xlsx")


            empty_fig = ff.create_gantt(
                df_example,
                colors=color_scale,
                index_col=selected_index_col,
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True,
                # show_hover_fill=False,
                
            )
            
            # fig.update_layout(legend=dict(title=dict(text="Priority/Status/Percentage")))

            return html.Div(
                dcc.Graph(figure=empty_fig),
                id="gantt-chart",
                className="gantt-chart-div",
            )

        df_input_data = pd.DataFrame(input_data)
        
        fig = ff.create_gantt(
            df_input_data,
            colors=color_scale,
            index_col=selected_index_col,
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            # show_hover_fill=False,
            height=800

        )
        
        start_date = pd.to_datetime(df_input_data['Start'].min())
        end_date = pd.to_datetime(df_input_data['Finish'].max())
        delta = end_date - start_date

        # Add hollow lines for each day
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            fig.add_shape(type="line",
                        x0=day, y0=-0.5, x1=day, y1=23.5,
                        line=dict(color="#2b2b2b", width=0.75, dash="dot"))

        # Add a red line for the current date
        current_date = datetime.now(pytz.timezone("Asia/Jakarta"))
        fig.add_shape(type="line",
                    x0=current_date, y0=-0.5, x1=current_date, y1=23.5,
                    line=dict(color="#220CFF", width=2))
        
        # fig.update_layout(legend=dict(title=dict(text="Priority/Status/Percentage")))
        
        return html.Div(
            dcc.Graph(figure=fig),
            id="gantt-chart",
            className="gantt-chart-div",
        )

    return html.Div(
        id="gantt-chart",
        className="gantt-chart-div",
    )
    
# Zara assistant



def chatbot_component():
    return html.Div([
        html.P('Zara AI Assistant', className='desc-zara-1', style={'marginBottom':'30px'}),
        dmc.Textarea(
            placeholder='Ask anything!',
            autosize=False,
            minRows=2,
            id='question',
            style={'margin-bottom':'10px'}
        ),
        dmc.Group(children=[
            dmc.Button(
                'Submit',
                id='chat-submit',
                disabled=True),
            dmc.Checkbox(id='checkbox-plotting', label='Enable plotting'),
            dmc.Checkbox(id='checkbox-pandasai', label='Enable query')
        ]),
        dmc.LoadingOverlay(
            html.Div(id='chat-output')
        )
    ], className='chat-container')
    
@callback(Output("chat-submit", "disabled"), Input("question", "value"))
def disable_submit(question):
    return not bool(question)

@callback(
    Output('chat-output', 'children'),
    Output('question','value'),
    Input('chat-submit', 'n_clicks'),
    Input('memory-input', 'data'),
    State('question', 'value'),
    State('chat-output', 'children'),
    State('checkbox-plotting', 'checked'),
    State('checkbox-pandasai', 'checked'),
    prevent_initial_call=True
)

def chat_window(n_clicks, data, question, cur, plotting_enabled, query_enabled):
    if 'file' in data:
        return cur, None
    
    if question:
        df = pd.DataFrame(data)
        prompt_content = prompt.generate_prompt(df, question)
        
        if query_enabled:
            df_pandasai = SmartDataframe(data, config={'llm':llm})
            pandasai_resp = df_pandasai.chat(question)
            
            if isinstance(pandasai_resp, SmartDataframe):
                
                # bot_table_output = f"{pandasai_resp}"
                # df_ = pd.read_csv(StringIO(bot_table_output), delim_whitespace=True, header=0, index_col=0)
                # df_.reset_index(inplace=True)
                
                markdown_output = pandasai_resp.to_markdown()
            else:
                markdown_output = str(pandasai_resp)
            
            question = [
                dcc.Markdown(question, className='chat-item question'),
                dcc.Markdown(markdown_output, className='chat-item answer')
                ]
            
            return (question + cur if cur else question), None
        
        if plotting_enabled:
            chart = cg.Chart(df, api_key=openai.api_key)
            fig = chart.plot(question, return_fig=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            
            graph_bot = dcc.Graph(figure=fig)
            question = [
                dcc.Markdown(question, className='chat-item question'),
                html.Div(
                    html.Div(graph_bot)
                )
            ]
            
            # div_plot = html.Div(graph_bot)
            
            return (question + cur if cur else question), None
        
        else:
            completion = openai.ChatCompletion.create(
                model='gpt-4', messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                                                {'role': 'user', 'content': prompt_content}]
            )
            
            question = [
                dcc.Markdown(question, className="chat-item question"),
                dcc.Markdown(
                    completion.choices[0].message.content, className="chat-item answer")
            ]
            
            return (question + cur if cur else question), None
    else:
        return [], None


# front end
app = Dash(
    __name__,
    prevent_initial_callbacks="initial_duplicate",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
app.title = "Geosurvai"

# app.layout = create_layout(app, data)
app.layout = html.Div(
    children = [
        jumbotron(),
        stepper(),
        upload_modals(),
        dmc.Grid(children=[
            dmc.Col(preview_table(), span='auto'),
            dmc.Col(chatbot_component(), span='auto')
        ], gutter='md'),
        # preview_table(),
        filter_value(),
        create_chart(),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True, port=8000)
