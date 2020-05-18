# def update_image(url, namespace, service_name, image_id, base_path, username, password):
#     return "更新镜像成功"
"""
参考文档: https://k8smeetup.github.io/docs/tasks/administer-cluster/access-cluster-api/
# 得到 apiserver的信息(地址和token)
kubectl config view
"""
from kubernetes import client


# aToken = "QmFzaWMgTlVaRE5qY3hRVUkzTWtJeE16bEdNelZHTkVJNlpqUlRXbTFXY2paclpWTjZPVGxvUWxCMVRHcEtiVlpFTVV4cFVrMHlUVkJTYlRsTmRVWTBUUT09"
# aConfiguration = client.Configuration()
# aConfiguration.host = "https://192.168.71.223:8765/r/projects/1a5/kubernetes:6443"
# aConfiguration.verify_ssl = False
# aConfiguration.api_key = {"authorization": "Bearer " + aToken}
# aApiClient = client.ApiClient(aConfiguration)
#
# # 更新pod的镜像id
# deployment_name = "servicemail"
# namespace = "default"
# image_id = ""
#
# apps_v1beta1 = client.AppsV1beta1Api(aApiClient)
# deployment_data = apps_v1beta1.read_namespaced_deployment(namespace=namespace, name=deployment_name)
# print(deployment_data)
# deployment_data.spec.template.spec.containers[
#     0].image = image_id
# api_response = apps_v1beta1.patch_namespaced_deployment(
#     name=deployment_name,
#     namespace=namespace,
#     body=deployment_data)
# print(api_response)


class MyK8s(object):
    def __init__(self, host, token):
        a_configuration = client.Configuration()
        a_configuration.host = host
        a_configuration.verify_ssl = False
        a_configuration.api_key = {"authorization": "Bearer " + token}
        a_api_client = client.ApiClient(a_configuration)
        apps_v1beta1 = client.AppsV1beta1Api(a_api_client)
        self.apps_v1beta1 = apps_v1beta1

    def update_image(self, namespace, name, image_id):
        deployment_data = self.apps_v1beta1.read_namespaced_deployment(namespace=namespace, name=name)
        deployment_data.spec.template.spec.containers[0].image = image_id
        self.apps_v1beta1.patch_namespaced_deployment(
            name=name,
            namespace=namespace,
            body=deployment_data)
        return "更新镜像成功"

    def get_cur_image_id(self, namespace, name):
        deployment_data = self.apps_v1beta1.read_namespaced_deployment(namespace=namespace, name=name)
        return deployment_data.spec.template.spec.containers[0].image
