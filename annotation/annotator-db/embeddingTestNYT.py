import pandas as pd
from sentence_transformers import SentenceTransformer
import time

model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
fileRead = "./data/NYT_Data_Raw_1_2000_to_12_2002.csv"
print("Reading " + fileRead)
article_df = pd.read_csv(fileRead)
print(article_df)

headlines = article_df["main_headline"].tolist()

startTime = time.time()
print("Generating Embeddings")
embeddings = model.encode(headlines)
endTime = time.time()
elapsedTime = endTime - startTime
print("Finished Generating Embeddings")