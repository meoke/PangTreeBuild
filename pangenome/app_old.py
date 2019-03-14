# -*- coding: utf-8 -*-

import dash
import shutil

import json
import pandas as pd
import flask

from app_style import external_css
from fileformats.json.JSONPangenome import JSONProgramParameters

from pang_run import run_pang, decode_json
from dash_app_components import consensus_tree
from dash_app_components import consensus_table
from dash_app_components import consensus_node
from dash_app_components import pangraph

from pang.fileformats.json import reader as pangenomejson_reader, writer as pangenomejson_writer

from networkx.readwrite import json_graph
import jsonpickle
import app_layout
import dash_html_components as html

# app = dash.Dash(__name__)
# app.title = 'pang'
# app.layout = app_layout.get_layout(app.get_asset_url)


# @app.callback(
#     dash.dependencies.Output('hidden_last_clicked', 'children'),
#     [dash.dependencies.Input('pang_button', 'n_clicks'),
#      dash.dependencies.Input('load_pangenome', 'n_clicks')],
#     [dash.dependencies.State('hidden_last_clicked', 'children')]
# )
# def trigger_pangenome_reload(run_pang_n_clicks, load_pangenome_n_clicks, last_clicked_jsonified):
#     if last_clicked_jsonified is None:
#         if run_pang_n_clicks == 1:
#             a = str(json.dumps([1, 0, 'run_pang']))
#             return a
#         if load_pangenome_n_clicks == 1:
#             return json.dumps([0, 1, 'load_pangenome'])
#     last_clicked = json.loads(last_clicked_jsonified)
#     if run_pang_n_clicks and last_clicked[0] == run_pang_n_clicks - 1:
#         return json.dumps([last_clicked[0]+1, last_clicked[1], 'run_pang'])
#     if load_pangenome_n_clicks and last_clicked[1] == load_pangenome_n_clicks - 1:
#         return json.dumps([last_clicked[0], last_clicked[1]+1, 'load_pangenome'])
#     return json.dumps([0, 0, ''])


@app.callback(
    dash.dependencies.Output('simple_consensus_params', 'style'),
    [dash.dependencies.Input('algorithm', 'value')])
def show_simple_consensus_algorithm_options(consensus_algorithm):
    if consensus_algorithm == 'simple':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('tree_consensus_params', 'style'),
    [dash.dependencies.Input('algorithm', 'value')])
def show_tree_consensus_algorithm_options(consensus_algorithm):
    if consensus_algorithm == 'tree':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
    dash.dependencies.Output('json_download', 'disabled'),
    [dash.dependencies.Input('hidden_pang_result', 'children')])
def download_json_button(_):
    return False


# @app.callback(
#     dash.dependencies.Output('hidden_pang_result', 'children'),
#     [dash.dependencies.Input('hidden_last_clicked', 'children')],
#     [dash.dependencies.State('pangenome_upload', 'contents'),
#      dash.dependencies.State('maf_upload', 'contents'),
#      dash.dependencies.State('metadata_upload', 'contents'),
#      dash.dependencies.State('pang_options', 'values'),
#      dash.dependencies.State('algorithm', 'value'),
#      dash.dependencies.State('hbmin', 'value'),
#      dash.dependencies.State('r', 'value'),
#      dash.dependencies.State('multiplier', 'value'),
#      dash.dependencies.State('stop', 'value'),
#      dash.dependencies.State('tree_consensus_options', 'values')
#      ])
# def call_pang(last_clicked,
#               pangenome_contents,
#               maf_contents,
#               metadata_contents,
#               pang_options_values,
#               consensus_algorithm_value,
#               hbmin_value,
#               r_value,
#               multiplier_value,
#               stop_value,
#               tree_consensus_options_values):
#     last_clicked = json.loads(last_clicked)
#     if last_clicked[2] == 'load_pangenome':
#         return decode_json(pangenome_contents[0])
#     else:
#         fasta_option = True if 'FASTA' in pang_options_values else False
#         re_consensus_value = True if 're_consensus' in tree_consensus_options_values else False
#         anti_fragmentation_value = True if 'anti_fragmentation' in tree_consensus_options_values else False
#         no_multiplier_anti_granular = True  # todo
#         pangenome, json_path = run_pang(maf_contents,
#                                         metadata_contents,
#                                         fasta_option,
#                                         consensus_algorithm_value,
#                                         hbmin_value,
#                                         r_value,
#                                         multiplier_value,
#                                         stop_value,
#                                         re_consensus_value,
#                                         anti_fragmentation_value,
#                                         no_multiplier_anti_granular)
#
#         shutil.copy(json_path, "download/pangenome.json")
#         return pangenomejson_writer.pangenome_to_json(pangenome)


# @app.callback(
#     dash.dependencies.Output('program_parameters_display', 'children'),
#     [dash.dependencies.Input('hidden_pang_result', 'children')]
# )
# def update_program_parameters(jsonified_pangenome):
#     jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
#     if jsonpangenome.program_parameters:
#         params: JSONProgramParameters = jsonpangenome.program_parameters
#         return [html.P(f"Multialignment path: {params.multialignment_file_path}"),
#                 html.P(f"Metadata path: {params.metadata_file_path}"),
#                 html.P(f"Not dag: {params.not_dag}"),
#                 html.P(f"Generate fasta: {params.generate_fasta}"),
#                 html.P(f"Consensus type: {params.consensus_type}"),
#                 html.P(f"(Simple consensus) HBMIN: {params.hbmin}"),
#                 html.P(f"(Tree consensus) Max cutoff strategy: {params.max_cutoff_strategy}"),
#                 html.P(f"(Tree consensus) Node cutoff strategy: {params.node_cutoff_strategy}"),
#                 html.P(f"(Tree consensus, MAX1) Range: {params.r}"),
#                 html.P(f"(Tree consensus, NODE1, NODE2) Multiplier: {params.multiplier}"),
#                 html.P(f"(Tree consensus) Stop: {params.stop}"),
#                 html.P(f"(Tree consensus) Re_consensus: {params.re_consensus}"),
#
#                 html.P(f"Fasta_complementation: {params.fasta_complementation_option}"),
#                 html.P(f"Local fasta dir: {params.local_fasta_dirpath}")
#                 ]

#
# @app.callback(
#     dash.dependencies.Output('hidden_consensus_tree_data', 'children'),
#     [dash.dependencies.Input('hidden_pang_result', 'children'),
#      dash.dependencies.Input('consensus_tree_graph', 'clickData')],
#     [dash.dependencies.State('hidden_consensus_tree_data', 'children')])
# def update_consensus_graph_data(jsonified_pangenome, click_data, old_jsonfied_consensus_tree):
#     old_tree = None
#     if old_jsonfied_consensus_tree:
#         old_tree = json_graph.tree_graph(jsonpickle.decode(old_jsonfied_consensus_tree))
#
#     jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
#     tree = consensus_tree.get_tree(jsonpangenome, click_data, old_tree)
#     jsonified_tree = json_graph.tree_data(tree, root=0)
#     return jsonpickle.encode(jsonified_tree)


# @app.callback(
#     dash.dependencies.Output('consensus_tree', 'style'),
#     [dash.dependencies.Input('consensus_tree_graph', 'figure')])
# def show_graph(_):
#     return {'display': 'block'}


@app.callback(
    dash.dependencies.Output('hidden_consensuses_table_data', 'children'),
    [dash.dependencies.Input('hidden_consensus_tree_data', 'children'),
     dash.dependencies.Input('consensus_tree_slider', 'value')],
    [dash.dependencies.State('hidden_pang_result', 'children')]
)
def update_consensuses_table(jsonified_consensus_tree, slider_value, jsonified_pangenome):
    tree = json_graph.tree_graph(jsonpickle.decode(jsonified_consensus_tree))
    jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
    consensus_table_data = consensus_table.get_consensus_table_data(jsonpangenome, tree, slider_value)
    consensus_table_data.to_csv('tabela.csv')
    return consensus_table_data.to_json()

#
# @app.callback(
#     dash.dependencies.Output('consensuses_table', 'data'),
#     [dash.dependencies.Input('hidden_consensuses_table_data', 'children')]
# )
# def update_consensuses_table_rows(jsonified_consensuses_table_data):
#     table_data = pd.read_json(jsonified_consensuses_table_data)
#     return consensus_table.table_to_rows_json(table_data)


# @app.callback(
#     dash.dependencies.Output('consensuses_table', 'columns'),
#     [dash.dependencies.Input('hidden_consensuses_table_data', 'children')]
# )
# def update_consensuses_table_columncs(jsonified_consensuses_table_data):
#     table_data = pd.read_json(jsonified_consensuses_table_data)
#     return [{"name": i, "id": i} for i in table_data.columns]


@app.callback(
    dash.dependencies.Output('consensus_tree_slider_value', 'children'),
    [dash.dependencies.Input('consensus_tree_slider', 'value')]
)
def show_slider_value(slider_value):
    return f"Slider value: \n{slider_value}."


# @app.callback(
#     dash.dependencies.Output('consensus_tree_graph', 'figure'),
#     [dash.dependencies.Input('hidden_consensus_tree_data', 'children'),
#      dash.dependencies.Input('consensus_tree_slider', 'value')],
#     [dash.dependencies.State('hidden_pang_result', 'children')])
# def update_consensus_tree_graph(jsonified_consensus_tree, slider_value,  jsonified_pangenome):
#     jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
#     tree = json_graph.tree_graph(jsonpickle.decode(jsonified_consensus_tree))
#     return consensus_tree.get_consensus_tree_graph(jsonpangenome, tree, slider_value)
#

# @app.callback(
#     dash.dependencies.Output('consensuses_table', 'style_data_conditional'),
#     [dash.dependencies.Input('hidden_consensuses_table_data', 'children')],
#     [dash.dependencies.State('hidden_consensus_tree_data', 'children')]
# )
# def color_consensuses_table_cells(jsonified_consensuses_table_data, jsonified_consensus_tree):
#     tree = json_graph.tree_graph(jsonpickle.decode(jsonified_consensus_tree))
#     table_data = pd.read_json(jsonified_consensuses_table_data)
#     return consensus_table.get_cells_styling(tree, table_data)


@app.callback(
    dash.dependencies.Output('hidden_csv_generated', 'children'),
    [dash.dependencies.Input('hidden_consensus_tree_data', 'children')],
    [dash.dependencies.State('hidden_csv_generated', 'children'),
     dash.dependencies.State('hidden_pang_result', 'children')]
)
def generate_csv_file(jsonified_consensus_tree, csv_generated, jsonified_pangenome):
    if csv_generated is None:
        consensus_tree = json_graph.tree_graph(jsonpickle.decode(jsonified_consensus_tree))
        jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
        csv_content = consensus_table.get_consensuses_table(jsonpangenome, consensus_tree)
        csv_content.to_csv("download/consensus.csv")
        return json.dumps(True)
    else:
        return json.dumps(True)


# @app.callback(
#     dash.dependencies.Output('consensus_node_details', 'data'),
#     [dash.dependencies.Input('consensus_tree_graph', 'clickData')],
#     [dash.dependencies.State('hidden_consensus_tree_data', 'children'),
#      dash.dependencies.State('hidden_pang_result', 'children')]
# )
# def update_consensus_node_details(tree_click_data, jsonified_tree, jsonified_pangenome):
#     tree = json_graph.tree_graph(jsonpickle.decode(jsonified_tree))
#     jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
#     dash_table_data = consensus_node.get_details(tree_click_data, tree, jsonpangenome)
#     return dash_table_data


# @app.callback(
#     dash.dependencies.Output('consensus_node_details_header', 'children'),
#     [dash.dependencies.Input('consensus_tree_graph', 'clickData')]
# )
# def update_consensus_node_details_header(tree_click_data):
#     clicked_node = tree_click_data['points'][0]
#     node_id = clicked_node['pointIndex']
#     return f"Sequences assigned to consensus {node_id}:"


@app.callback(
    dash.dependencies.Output('hidden_pangraph_points', 'children'),
    [dash.dependencies.Input('hidden_pang_result', 'children')]
)
def update_pangraph_data_points(jsonified_pangenome):
    jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
    if jsonpangenome.nodes:
        pangraph_nodes_data = pangraph.get_nodes_data(jsonpangenome)
        return pangraph_nodes_data.to_json()


@app.callback(
    dash.dependencies.Output('hidden_pangraph_traces', 'children'),
    [dash.dependencies.Input('hidden_pang_result', 'children')]
)
def update_pangraph_traces(jsonified_pangenome):
    jsonpangenome = pangenomejson_reader.json_to_jsonpangenome(jsonified_pangenome)
    if jsonpangenome.nodes:
        pangraph_traces_data = pangraph.get_traces_data(jsonpangenome)
        return json.dumps(pangraph_traces_data)


@app.callback(
    dash.dependencies.Output('pangraph_graph', 'figure'),
    [dash.dependencies.Input('hidden_pangraph_points', 'children'),
     dash.dependencies.Input('hidden_pangraph_traces', 'children')]
)
def update_pangraph_data(jsonified_pangraph_points, jsonified_pangraph_traces):
    pangraph_nodes_data = pd.read_json(jsonified_pangraph_points)
    pangraph_traces_data = json.loads(jsonified_pangraph_traces)
    return pangraph.get_graph(pangraph_nodes_data, pangraph_traces_data)


@app.callback(
    dash.dependencies.Output('pangraph_display', 'style'),
    [dash.dependencies.Input('pangraph_graph', 'figure')])
def show_graph(_):
    return {'display': 'block'}


# @app.server.route('/download_pangenome')
# def download_json():
#     return flask.send_file('../download/pangenome.json',
#                            mimetype='text/csv',
#                            attachment_filename='pangenome.json',
#                            as_attachment=True)


# @app.server.route('/download_csv')
# def download_csv():
#     return flask.send_file('../download/consensus.csv',
#                            mimetype='text/csv',
#                            attachment_filename='consensus.csv',
#                            as_attachment=True)


# for css in external_css:
#     app.css.append_css({"external_url": css})

# if __name__ == '__main__':
#     app.run_server(debug=True, port=8052)