# Dockerfile
FROM public.ecr.aws/lambda/python:3.13

# Copy app and install deps
COPY requirements.txt   /var/task/
RUN  pip install -r /var/task/requirements.txt

# Copy your code
COPY .   /var/task/

# Set handler
CMD ["lambda_function.lambda_handler"]
