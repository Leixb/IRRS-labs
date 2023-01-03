import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt 
import plotly.graph_objects as go 

'''G = nx.watts_strogatz_graph(n=40, k=4, p=0.98)

cc = nx.average_clustering(G)
asp = nx.average_shortest_path_length(G)
cc_values = []
asp_values = []
p_values=[]
nx.draw_networkx(G)
#fig = go.Figure(G) 
#plt.show()
'''
'''In a Barabasi-Albert (BA) network, the degree distribution follows a power law, which means that the probability of a node having a certain degree
 (i.e., the number of edges it is connected to) is inversely proportional to the degree raised to some power (typically denoted by γ).

The BA model is a generative model for growing networks that starts with a small number of nodes and gradually adds new nodes over time. 
Each new node is connected to m existing nodes with a probability proportional to the degree of the existing nodes. This process results in a scale-free network, 
where the degree distribution follows a power law of the form:

P(k) ∝ k^-γ

where P(k) is the probability of a node having degree k, and γ is the power-law exponent.

The power-law exponent γ for a BA network is typically around 2.1. This means that the probability of a node having a high degree decreases rapidly with increasing

degree. In other words, there are relatively few nodes with a high degree (i.e., many edges) compared to the number of nodes with a low degree.

The power-law degree distribution of a BA network is a result of the preferential attachment mechanism, which gives higher probability to nodes with a high degree 
to attract new edges. This leads to the formation of a few highly connected nodes (hubs) that dominate the network, and a large number of low-degree nodes.

The Barabasi-Albert (BA) model is a generative model for growing networks that is used to study the structure and properties of real-world networks. 
It is a simple model that captures some of the key features of many real-world networks, such as the presence of highly connected nodes  and 
the power-law degree distribution.

The BA model starts with a small number of nodes and gradually adds new nodes over time. Each new node is connected to m existing nodes with
a probability proportional to the degree of the existing nodes. This process results in a scale-free network, where the degree distribution follows
a power law (i.e., the probability of a node having a certain degree is inversely proportional to the degree raised to some power).
  
The degree distribution of most real-world networks follows a power-law distribution.

'''

n = 100
m = 2
G_barabasi = nx.barabasi_albert_graph(n,m)

degree_freq = nx.degree_histogram(G_barabasi)
degrees = range(len(degree_freq))
plt.figure(figsize=(12, 8)) 
plt.loglog(degrees[m:], degree_freq[m:],'go-') 
plt.xlabel('Degree')
plt.ylabel('Frequency')
plt.show()