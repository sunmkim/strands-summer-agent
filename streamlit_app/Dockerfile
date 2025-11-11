FROM public.ecr.aws/docker/library/python:3.13-slim

WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install requirements
RUN pip3 install -r requirements.txt

# Expose the port that Streamlit runs on
EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]