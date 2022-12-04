import pandas as pd
from flask import Flask, render_template, request, Response
import io


from ml import Model

ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/get_prediction", methods=['POST'])
def check_eligibility():
    try:
        data = request.form
        model = Model()
        file = request.files['customers']

        if file.filename == '':
            raise Exception('No file provided')

        if not(allowed_file(file.filename)):
            raise Exception('Not valid extension')

        customers = pd.read_csv(file)

        prediction = model.predict(customers)
        prediction = prediction[['CustomerId', 'PipedriveId', 'Churned']]
        prediction.Churned = prediction.Churned.replace(0, 'No').replace(1, 'Yes')

        prediction.to_csv('assets/prediction.csv', index=False)
        return render_template('result.html', result=prediction)

    except Exception as e:
        return render_template('index.html', error=True, message=e)


@app.route("/get_csv")
def get_csv():

    s = io.StringIO()
    df = pd.read_csv('assets/prediction.csv')
    df.to_csv(s)
    csv = s.getvalue()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=prediction.csv"})


@app.route("/")
@app.route('/index')
def index():
    return render_template('index.html')
