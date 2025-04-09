
    graph_image = graph.get_graph(xray=True).draw_mermaid_png()
    # Save the graph image to a file and display it
    output_path = "/home/lumasty/Documents/GitHub/MAFinancialAssistance/SuperviseAgent/graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)
    print(f"Graph image saved to {output_path}")