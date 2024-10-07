import json
import pandas as pd
import streamlit as st
from pyvis.network import Network
import networkx as nx
from streamlit.components.v1 import html

# 用于将树形结构转化为表格的函数
def create_table_from_tree(data):
    rows = []
    
    # 遍历每个对象
    for item in data:
        name = item.get('name', 'Unknown')
        father = item.get('father', 'Unknown')
        definition = item.get('definition', 'No definition available')
        total_descendants = item.get('total_descendants', 0)
        scores = item.get('scores', {})
        level = item.get('level', 0)
        
        # 为每个节点创建一行数据
        row = {
            'Name': name,
            'Father': father,
            'Definition': definition,
            'Total Descendants': total_descendants,
            'Level': level
        }
        
        # 将每个分数添加到行中
        for score_type, score_value in scores.items():
            row[score_type] = score_value
        
        # 将行添加到表格中
        rows.append(row)

    # 创建一个DataFrame
    df = pd.DataFrame(rows)
    return df

# 用于生成和展示交互式树形图的函数
def create_interactive_tree(data):
    # 创建 NetworkX 图
    G = nx.DiGraph()

    # 添加根节点
    root_node = "obj"
    G.add_node(root_node, definition="Root node for all objects")

    # 遍历数据，添加节点和边
    for item in data:
        name = item['name']
        father = item['father']
        
        # 创建描述信息，包括得分
        if item["scores"]["clip_score_scores"]:
            scores_str = "\n".join([f"{k}: {v:.4f}" for k, v in item['scores'].items()])
        else:
            scores_str = "\n".join([f"{k}: {"null"}" for k, v in item['scores'].items()])
            
            
        tooltip = f"{item['definition']}\n\nScores:\n{scores_str}"
        
        # 添加节点
        G.add_node(name, title=tooltip, total_descendants=item['total_descendants'])
        G.add_edge(father, name)

    # 使用 Pyvis 创建交互式网络
    net = Network(height="750px", width="100%", directed=True)

    # 将 NetworkX 图添加到 Pyvis
    net.from_nx(G)

    # 保存 HTML 文件
    net.save_graph("interactive_tree.html")

    # 读取 HTML 文件内容
    with open("interactive_tree.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    return html_content
# 用于递归查找父节点及其所有子孙节点的函数
def find_descendants(df, selected_father):
    descendants = set()  # 用于存储所有的子孙节点
    queue = [selected_father]  # 从父节点开始
    while queue:
        current_father = queue.pop(0)
        descendants.add(current_father)
        # 查找当前父节点的直接子节点
        children = df[df['Father'] == current_father]['Name'].tolist()
        queue.extend(children)
    return descendants
# Streamlit 主程序
def main():
    st.title("Interactive JSON Object Hierarchy with Table")

    # 上传多个JSON文件
    uploaded_files = st.file_uploader("Upload JSON file", accept_multiple_files=True, type=["json"])

    # 用于存储所有 JSON 文件中的数据
    data = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # 读取每个 JSON 文件
            file_data = json.load(uploaded_file)
            data.extend(file_data)

        # 生成交互式树形图
        interactive_html = create_interactive_tree(data)
        # 使用Streamlit的HTML组件嵌入交互图
        st.components.v1.html(interactive_html, height=800)

        # 生成树形结构的表格
        # 生成树形结构的表格
        df = create_table_from_tree(data)

        # 获取用户定义的 Level 过滤范围，默认范围是 0 到 最高层级
        min_level, max_level = st.slider(
            'Select Level Range:',
            int(df['Level'].min()), int(df['Level'].max()), (0, int(df['Level'].max()))
        )

        # 根据选择的 Level 范围进行过滤
        filtered_df = df[(df['Level'] >= min_level) & (df['Level'] <= max_level)]

        # 获取所有 unique 的 father 并创建筛选框
        father_options = ['All'] + sorted(filtered_df['Father'].unique().tolist())
        selected_father = st.selectbox('Select Father:', father_options)

        # 如果选择了特定的 Father 而不是 "All"，则进一步过滤
        if selected_father != 'All':
            # 递归找到所有子孙节点
            descendants = find_descendants(df, selected_father)
            # 筛选出父节点及其所有子孙节点
            filtered_df = filtered_df[filtered_df['Name'].isin(descendants)]

        # 在Streamlit中展示过滤后的表格
        st.dataframe(filtered_df)

        # 提供表格的下载按钮
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="filtered_tree_structure.csv", mime="text/csv")

    else:
        st.write("Upload JSON files")

if __name__ == "__main__":
    main()