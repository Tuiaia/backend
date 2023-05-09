FROM python:3.9.6
COPY ./requirements.txt ./
RUN pip3 install -r requirements.txt
COPY ./ /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "15400", "--reload" ]