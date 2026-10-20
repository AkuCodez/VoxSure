"""Rebuild ml/notebooks/VoxSure_Train_Colab.ipynb from the CURRENT dataset/training scripts (self-contained, no repo needed).
Run:  python ml/scripts/make_colab_notebook.py
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parent
OUT = R.parent / "notebooks" / "VoxSure_Train_Colab.ipynb"


def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.splitlines(True)}
def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(True)}


build = (R / "build_dataset.py").read_text(encoding="utf-8")
train = (R / "train_intent.py").read_text(encoding="utf-8")
cells = [
    md("# VoxSure: intent model training (Colab)\nTrains the same fine-tuned DistilBERT used in the app, from the same dataset builder.\n\n"
       "Runtime > Change runtime type > **T4 GPU** is optional (CPU also works). Steps: install, build dataset, train, held-out check, download `intent_model.zip` "
       "and put its contents in `ml/artifacts/intent_model/` of the repo.\n\n"
       "The dataset is author-written (see `ml/data/README.md` in the repo); the numbers printed here are the held-out TEST split."),
    code("!pip -q install transformers==4.47.1 scikit-learn\nimport os\nos.makedirs('ml/scripts', exist_ok=True); os.makedirs('ml/data', exist_ok=True); os.makedirs('ml/artifacts', exist_ok=True)"),
    code("%%writefile ml/scripts/build_dataset.py\n" + build),
    code("%%writefile ml/scripts/train_intent.py\n" + train),
    code("!python ml/scripts/build_dataset.py"),
    code("!python ml/scripts/train_intent.py --epochs 6 --seed 42"),
    md("## Held-out check (test split: never used for training or tuning)"),
    code("""import json, torch
from sklearn.metrics import f1_score, accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
d='ml/artifacts/intent_model'
tok=AutoTokenizer.from_pretrained(d); m=AutoModelForSequenceClassification.from_pretrained(d).eval()
labels=json.load(open(d+'/label_map.json')); l2i={l:i for i,l in enumerate(labels)}
test=[json.loads(l) for l in open('ml/data/test.jsonl')]
pred=[]
with torch.no_grad():
    for i in range(0,len(test),64):
        b=tok([r['text'] for r in test[i:i+64]],padding=True,truncation=True,max_length=48,return_tensors='pt')
        pred+=m(**b).logits.argmax(1).tolist()
y=[l2i[r['intent']] for r in test]
print('accuracy',round(accuracy_score(y,pred),3),'macro-F1',round(f1_score(y,pred,average='macro'),3))"""),
    code("!cd ml/artifacts && zip -qr intent_model.zip intent_model\nfrom google.colab import files\nfiles.download('ml/artifacts/intent_model.zip')"),
]
nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"}}, "nbformat": 4, "nbformat_minor": 0}
OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT, f"({len(cells)} cells)")
