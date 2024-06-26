import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_curve, roc_auc_score

import classification


def trained_clustering_model(data, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(data)
    return kmeans


def tune_clustering_hyperparameter(data):
    # candidates' range of n_clusters
    range_n_clusters = range(2, 30)
    silhouette_avg = pd.Series()

    # use silhouette score
    for n_clusters in range_n_clusters:
        # initialize k means
        kmeans = trained_clustering_model(data, n_clusters)
        # silhouette scores
        silhouette_avg.loc[n_clusters] = silhouette_score(data, kmeans.labels_)

    # when silhouette score is highest, k is optimal
    return silhouette_avg.idxmax()


def visualize_clustering(model, data, n_clusters, silhouette_avg, label):
    # analyze using plotting

    # visualize silhouette plot and scatter plot as subplots
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_size_inches(18, 7)

    # calculate cluster results
    cluster_labels = model.predict(data)

    # plot
    set_silhouette_subplot(ax1, model, data, n_clusters, cluster_labels, silhouette_avg)
    set_scatter_subplot(ax2, model, data, n_clusters, cluster_labels)
    plt.suptitle(
        f"For {label} data\nSilhouette analysis for KMeans clustering\nwith n_clusters = %d" % n_clusters,
        fontsize=14,
        fontweight='bold'
    )
    plt.show()


def set_silhouette_subplot(subplot, model, data, n_clusters, cluster_labels, silhouette_avg):
    # this subplot is the silhouette plot
    subplot.set_xlim([-0.2, 1])
    # The (n_clusters+1)*10 is for inserting blank space between silhouette plot
    subplot.set_ylim([0, len(data) + (n_clusters + 1) * 10])

    # Compute the silhouette scores for each sample
    sample_silhouette_values = silhouette_samples(data, model.labels_)

    y_lower = 10
    for i in range(n_clusters):
        # Aggregate the silhouette scores
        ith_cluster_silhouette_values = sample_silhouette_values[cluster_labels == i]

        ith_cluster_silhouette_values.sort()

        size_cluster_i = ith_cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster_i

        color = cm.nipy_spectral(float(i) / n_clusters)
        subplot.fill_betweenx(
            np.arange(y_lower, y_upper),
            0,
            ith_cluster_silhouette_values,
            facecolor=color,
            edgecolor=color,
            alpha=0.7
        )

        # Label the silhouette plots with their cluster numbers at the middle
        subplot.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))
        # Compute the new y_lower for next plot
        y_lower = y_upper + 10

        subplot.set_title(f"Number of Cluster: {n_clusters}\nSilhouette Score: {round(silhouette_avg, 3)}")
        subplot.set_xlabel("The silhouette coefficient values")
        subplot.set_ylabel("Cluster label")

        # The vertical line for average silhouette score of all the values
        subplot.axvline(x=silhouette_avg, color="red", linestyle="--")

        subplot.set_yticks([])  # Clear the yaxis labels / ticks
        subplot.set_xticks([-0.2, 0, 0.2, 0.4, 0.6, 0.8, 1])


def set_scatter_subplot(subplot, model, train_data, n_clusters, cluster_labels):
    # convert multi-dimension data to 2 dimension for visualizing to scatter plot
    pca = PCA(n_components=2)
    pca_data = pd.DataFrame(data=pca.fit_transform(train_data), columns=['PC1', 'PC2'])
    pca_data['cluster'] = cluster_labels

    # Plot showing the actual clusters formed
    colors = cm.nipy_spectral(cluster_labels.astype(float) / n_clusters)
    subplot.scatter(data=pca_data, x='PC1', y='PC2', marker='.', s=30, lw=0, alpha=0.7, c=colors, edgecolor='k')

    subplot.set_title("The visualization of the clustered data.")
    subplot.set_xlabel("Principal Component 1")
    subplot.set_ylabel("Principal Component 2")


def evaluate_analyze_clustering(data, label='all'):
    # Z-score scaling
    data_scaled = StandardScaler().fit_transform(data)

    # calculate optimal k (n_clusters)
    k = tune_clustering_hyperparameter(data_scaled)

    # train model
    clustering_model = trained_clustering_model(data_scaled, k)

    # evaluate model using silhouette score
    # worst: -1.0, best: 1.0
    # show this value in plot graph subtitle
    score = silhouette_score(data_scaled, clustering_model.labels_)

    # analyze model using plotting
    visualize_clustering(clustering_model, data_scaled, k, score, label)


def k_fold_cv_knn(X, y, n_neighbors):
    # evaluate using 10-fold cross validation
    kfold = KFold(10, shuffle=True, random_state=42)
    accuracy = []

    for train_index, test_index in kfold.split(X, y):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        # Z-score scaling
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.fit_transform(X_test)

        # train knn classifier model
        knn = classification.KNNClassifier()
        knn.fit(pd.DataFrame(X_train_scaled, columns=X_train.columns), y_train)
        y_pred = [knn.predict(pd.DataFrame([X_test_scaled[i]], columns=X_test.columns), n_neighbors) for i in
                  range(X_test.shape[0])]

        # calculate accuracy
        accuracy.append(accuracy_score(y_test, y_pred))

    mean_accuracy = sum(accuracy) / len(accuracy)
    return mean_accuracy


def confusion_matrix_knn(y_test, y_pred):
    # analyze using confusion matrix
    matrix = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    return matrix, report


def visualize_roc_curve_knn(y_test, y_pred, label):
    # analyze using ROC curve
    fpr, tpr, thresholds = roc_curve(y_test, y_pred)
    plt.figure(figsize=(15, 5))

    # diagonal line
    plt.plot([0, 1], [0, 1], label='STR')
    # ROC curve
    plt.plot(fpr, tpr, label='ROC')

    plt.title(f"ROC curve of {label} data")
    plt.xlabel('False Positive Rate')
    plt.xlabel('True Positive Rate')
    plt.legend()
    plt.grid()
    plt.show()


def evaluate_analyze_knn(data, label='all'):
    # dec is target variable
    X = data.drop(['dec'], axis=1)
    y = data['dec']

    n_neighbors = 5

    # split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Z-score scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.fit_transform(X_test)

    # train and predict with knn classifier model
    knn = classification.KNNClassifier()
    knn.fit(pd.DataFrame(X_train_scaled, columns=X_train.columns), y_train)
    y_pred = [knn.predict(pd.DataFrame([X_test_scaled[i]], columns=X_test.columns), n_neighbors) for i in
              range(X_test.shape[0])]

    # evaluate model using 10-fold cross validation
    accuracy = k_fold_cv_knn(X, y, n_neighbors)
    print(f"\n\nAverage accuracy of {label} data using 10-Fold cross validation: {accuracy}")

    # analyze model using confusion matrix and ROC curve
    matrix, report = confusion_matrix_knn(y_test, y_pred)
    print(f"Confusion Matrix of {label} data:\n", matrix)
    print(f"Classification report of {label} data:\n", report)

    # analyze by plotting ROC curve
    visualize_roc_curve_knn(y_test, y_pred, label)

    # analyze using AUC (the area under the ROC curve)
    # best case: 1.0
    # worst case: 0.5
    auc = roc_auc_score(y_test, y_pred)
    print(f"AUC score of {label} data: {auc}")


# load preprocessed data
preprocessed_data = pd.read_csv('cleaned_speed_data.csv')

for col in preprocessed_data.columns:
    if preprocessed_data[col].dtype == 'bool':
        preprocessed_data[col] = preprocessed_data[col].astype(int)

# analyze all data
# clustering
evaluate_analyze_clustering(preprocessed_data)

# k nearest neighbors
evaluate_analyze_knn(preprocessed_data)

# analyze by gender
male_data = preprocessed_data[preprocessed_data['gender'] == 1]
female_data = preprocessed_data[preprocessed_data['gender'] == 0]

# clustering
evaluate_analyze_clustering(male_data, label='male')
evaluate_analyze_clustering(female_data, label='female')

# k nearest neighbors
evaluate_analyze_knn(male_data, label='male')
evaluate_analyze_knn(female_data, label='female')

# analyze by age
data_20_to_24 = preprocessed_data[(preprocessed_data['age'] >= 20) & (preprocessed_data['age'] < 25)]
data_25_to_29 = preprocessed_data[(preprocessed_data['age'] >= 25) & (preprocessed_data['age'] < 30)]
data_over_30 = preprocessed_data[preprocessed_data['age'] >= 30]

# clustering
evaluate_analyze_clustering(data_20_to_24, label='age from 20 to 24')
evaluate_analyze_clustering(data_25_to_29, label='age from 25 to 29')
evaluate_analyze_clustering(data_25_to_29, label='age over 30')

# k nearest neighbors
evaluate_analyze_knn(data_20_to_24, label='age from 20 to 24')
evaluate_analyze_knn(data_25_to_29, label='age from 25 to 29')
evaluate_analyze_knn(data_over_30, label='age over 30')
