FROM registry.cn-shenzhen.aliyuncs.com/yibainetwork/devops-platform-product:1512_201910161100
WORKDIR /usr/src/app
RUN rm -rf *
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [ "python", "./setup.py" ]