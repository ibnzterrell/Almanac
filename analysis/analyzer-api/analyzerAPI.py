from flask import Flask, request, g
from flask_cors import CORS, cross_origin
from scipy import signal, stats
import pandas as pd
from io import BytesIO
from sthu_peak import get_persistent_homology
import json

app = Flask(__name__)
CORS(app)


def findPeaks_All(df, y):
    peak_indices = signal.find_peaks(df[y])
    return peak_indices[0]


def findPeaks_MADP(df, y):
    # Use median absolute deviation instead of standard deviation for robustness
    mad = stats.median_abs_deviation(df[y])
    peak_indices = signal.find_peaks(df[y], prominence=mad)
    return peak_indices[0]


def findPeaks_PH(df, y):
    peaks = get_persistent_homology(df[y])
    peak_indicies = [p.born for p in peaks]
    return peak_indicies

def findPeaks(df, y, method):
    peakAlgo = {
        "all": findPeaks_All,
        "MADP": findPeaks_MADP,
        "PH": findPeaks_PH
    }
    return peakAlgo[method](df, y)

@app.route("/peaks", methods=["post"])
def peaks():
    req  = json.loads(request.data)
    x = req["x"]
    y = req["y"]
    method = req["method"]
    df = pd.DataFrame.from_records(req["data"])
    df.sort_values(by=[x])
    results = findPeaks(df, y, method)
    df = df.iloc[results]
    return df.to_json(orient="records")

@app.route("/valleys", methods=["post"])
def valleys():
    req  = json.loads(request.data)
    x = req["x"]
    y = req["y"]
    method = req["method"]
    df = pd.DataFrame.from_records(req["data"])
    df.sort_values(by=[x])
    df_invert = df.copy()
    df_invert[y] = df_invert[y].max() - df_invert[y] + df_invert[y].min()
    results = findPeaks(df_invert, y, method)
    df = df.iloc[results]
    return df.to_json(orient="records")

if __name__ == '__main__':
    app.run(port=3000)
