import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from sklearn.cluster import DBSCAN
from sklearn.manifold import TSNE
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.llms import OpenAI
from langchain import PromptTemplate
import numpy as np
import io
import os


def get_natural_convs_title(summaries):
    """
    Create few-word, topic-based summarization of a list of conversation summaries
    """
    llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
    docs = [Document(page_content=text) for text in summaries]
    prompt = """
    Write a title for the following summaries of conversations
    "{text}"
    TITLE:
    """
    prompt_template = PromptTemplate(template=prompt, input_variables=["text"])

    summarize_chain = load_summarize_chain(
        llm, chain_type="stuff", prompt=prompt_template)
    title = summarize_chain.run(docs)
    return title


def vis_convos(data, name):
    # Load the data from the JSON object
    # create a numpy array that is a list of all the embeddings

    embeddings = np.array([conv['embedding'] for conv in data])
    summaries = [conv['summary'] for conv in data]

    # Reduce the dimensionality of the vectors
    vectors_2d = TSNE(n_components=2, perplexity=min(len(data) - 2, 30)).fit_transform(
        embeddings)

    # Apply DBSCAN clustering
    db = DBSCAN(eps=0.5, min_samples=5).fit(vectors_2d)
    labels = db.labels_
    print("after dbscan")

    # Find the unique labels (cluster IDs).
    unique_labels = set(labels)

    titles = []

    # For each label...
    for label in unique_labels:
        # Get the indices of the points that belong to the current cluster.
        indices = [i for i, x in enumerate(labels) if x == label]

        # Get the summaries corresponding to these indices.
        cluster_summaries = [summaries[i] for i in indices]

        # Now, you have a list of all summaries associated with the current cluster.
        # Feed this list to your title-creating tool.

        # This is an example. Replace the following line with your actual tool.
        title = get_natural_convs_title(cluster_summaries)

        titles.append(title)

    # Create a scatter plot
    scatter = plt.scatter([v[0] for v in vectors_2d], [v[1]
                          for v in vectors_2d], c=labels, cmap='viridis')

    # Hide the axis
    plt.axis('off')

    # Get the centroid of each cluster and annotate
    centroids = [np.mean([vectors_2d[i] for i in range(
        len(vectors_2d)) if labels[i] == label], axis=0) for label in unique_labels]

    for centroid, title in zip(centroids, titles):
        plt.annotate(title, centroid)

    # add a title to this graph
    plt.title(f"""Cluster of {name}'s conversations""")

    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    return image_stream


def view_time_conversations(conversations, name):
    # Sort conversations based on start time
    sorted_conversations = sorted(
        conversations, key=lambda conv: conv["startTime"])

    # Create a figure and axis
    fig, ax = plt.subplots()

    # Dictionary to track y-values for each projectId
    project_y_values = {}

    # Plot each conversation as a horizontal line
    for conv in sorted_conversations:
        start_time = datetime.strptime(
            conv["startTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
        end_time = datetime.strptime(conv["endTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
        project_id = conv["projectId"]
        summary = conv["summary"]

        if project_id not in project_y_values:
            # Assign a new y-value for the projectId
            y = len(project_y_values) + 1
            project_y_values[project_id] = y
        else:
            # Reuse the existing y-value for the projectId
            y = project_y_values[project_id]

        # Convert start_time and end_time to float
        start_time_float = mdates.date2num(start_time)
        end_time_float = mdates.date2num(end_time)

        ax.plot([start_time_float, end_time_float], [y, y], marker="o")

        # Add summary text annotation
        ax.text(start_time_float, y, summary, ha='right', va='center')

    # Set y-axis limits
    ax.set_ylim(0.5, len(project_y_values) + 0.5)

    # Set y-axis ticks and labels
    y_ticks = list(range(1, len(project_y_values) + 1))
    # Use projectIds as y-axis labels
    y_labels = [str(project_id) for project_id in project_y_values.keys()]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)

    # Format x-axis labels
    date_format = "%A, %d %B %Y %H:%M"  # Example: Monday, 30 May 2023 10:00
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    plt.xticks(rotation=45)

    # Set axis labels and title
    ax.set_xlabel("Time")
    ax.set_ylabel("Project ID")  # Change y-axis label to "Project ID"
    ax.set_title(f"What {name} has been talking about")

    # plt.tight_layout()
    # plt.show()
    image_stream = io.BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    return image_stream