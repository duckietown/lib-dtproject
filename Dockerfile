FROM python:3.7

WORKDIR /library
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

RUN apt update && apt install -y --no-install-recommends git

COPY . .

ENV DISABLE_CONTRACTS=1

RUN find .

RUN python setup.py develop

# run it once to see everything OK
RUN python3 -c "import dtproject"
