import json
import pandas as pd
import streamlit as st
from pyvis.network import Network
import networkx as nx
from streamlit.components.v1 import html

def create_table_from_tree(data):
    rows = []
    
    for item in data:
        name = item.get('name', 'Unknown')
        father = item.get('father', 'Unknown')
        definition = item.get('definition', 'No definition available')
        total_descendants = item.get('total_descendants', 0)
        scores = item.get('scores', {})
        level = item.get('level', 0)
        
        row = {
            'Name': name,
            'Father': father,
            'Definition': definition,
            'Total Descendants': total_descendants,
            'Level': level
        }
        
        for score_type, score_value in scores.items():
            row[score_type] = score_value
        
        rows.append(row)

    df = pd.DataFrame(rows)
    return df

def create_interactive_tree(data):
    G = nx.DiGraph()

    root_node = "obj"
    G.add_node(root_node, definition="Root node for all objects")

    for item in data:
        name = item['name']
        father = item['father']
        
        if item["scores"]["clip_score_scores"]:
            scores_str = "\n".join([f"{k}: {v:.4f}" for k, v in item['scores'].items()])
        else:
            scores_str = "\n".join([f"{k}: {"null"}" for k, v in item['scores'].items()])
            
            
        tooltip = f"{item['definition']}\n\nScores:\n{scores_str}"
        
        G.add_node(name, title=tooltip, total_descendants=item['total_descendants'])
        G.add_edge(father, name)

    net = Network(height="750px", width="100%", directed=True)

    net.from_nx(G)


    net.save_graph("interactive_tree.html")


    with open("interactive_tree.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    return html_content
def find_descendants(df, selected_father):
    descendants = set()  
    queue = [selected_father]  
    while queue:
        current_father = queue.pop(0)
        descendants.add(current_father)
        children = df[df['Father'] == current_father]['Name'].tolist()
        queue.extend(children)
    return descendants

def main():
    st.title("Interactive JSON Object Hierarchy with Table")

    uploaded_files = st.file_uploader("Upload JSON file", accept_multiple_files=True, type=["json"])

    data = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_data = json.load(uploaded_file)
            data.extend(file_data)

        # # interactive tree
        # interactive_html = create_interactive_tree(data)
        # # html display
        # st.components.v1.html(interactive_html, height=800)


        df = create_table_from_tree(data)

        min_level, max_level = st.slider(
            'Select Level Range:',
            int(df['Level'].min()), int(df['Level'].max()), (0, int(df['Level'].max()))
        )

        filtered_df = df[(df['Level'] >= min_level) & (df['Level'] <= max_level)]

        father_options = ['All'] + sorted(filtered_df['Father'].unique().tolist())
        selected_father = st.selectbox('Select Father:', father_options)

        if selected_father != 'All':
            descendants = find_descendants(df, selected_father)
            filtered_df = filtered_df[filtered_df['Name'].isin(descendants)]

        st.dataframe(filtered_df)

        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="filtered_tree_structure.csv", mime="text/csv")

    else:
        st.write("Upload JSON files")

if __name__ == "__main__":
    main()
