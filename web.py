from kubernetes import client
from flask import Flask, render_template, request, jsonify, abort
from six import iteritems

app = Flask(__name__)


class KuberAPI:
    def __init__(self):
        pass

    Deployment = {'AppsV1beta1': 'AppsV1beta1Deployment',
                  'ExtensionsV1beta1': 'ExtensionsV1beta1Deployment',
                  'v1': 'V1Deployment'}

    Pod = {'v1': 'V1Pod'}

    ReplicaSet = {'v1': 'V1ReplicaSet',
                  'v1beta1': 'V1beta1ReplicaSet',
                  'v1beta2': 'V1beta2ReplicaSet'}

    ReplicationController = {'v1': 'V1ReplicationController'}

    StatefulSet = {'v1': 'V1StatefulSet',
                   'v1beta1': 'V1beta1StatefulSet',
                   'v1beta2': 'V1beta2StatefulSet'}

    Service = {'v1api': 'V1APIService',
               'v1': 'V1Service',
               'v1beta1': 'V1beta1APIService'}

    Volume = {'v1': 'V1Volume'}

    PersistentVolume = {'v1': 'V1PersistentVolume'}

    NameSpace = {'v1': 'V1Namespace'}

    DaemonSet = {'v1': 'V1DaemonSet',
                 'v1beta1': 'V1beta1DaemonSet',
                 'v1beta2': 'V1beta2DaemonSet'}

    Job = {'v1': 'V1Job'}

    CronJob = {'v1beta1': 'V1beta1CronJob',
               'v2alpha1': 'V2alpha1CronJob'}

    Role = {'v1': 'V1Role',
            'v1alpha1': 'V1alpha1Role',
            'v1beta1': 'V1beta1Role'}

    RoleBinding = {'v1beta1': 'V1beta1RoleBinding',
                   'v1alpha1': 'V1alpha1RoleBinding',
                   'v1': 'V1RoleBinding'}

    ClusterRole = {'v1': 'V1ClusterRole',
                   'v1alpha1': 'V1alpha1ClusterRole',
                   'v1beta1': 'V1beta1ClusterRole'}

    ClusterRoleBinding = {'v1beta1': 'V1beta1ClusterRoleBinding',
                          'v1alpha1': 'V1alpha1ClusterRoleBinding',
                          'v1': 'V1ClusterRoleBinding'}


class Leaves:
    def __init__(self, name, attr_name=None):
        self.has_child_attr = False
        self.__name__ = name
        self.attr_name = attr_name


class KuberParser:
    def __init__(self, Object=None, ObjectName=None, attr_name=None):
        self.has_child_attr = True
        self.is_list_attr = False
        if Object:
            self.object = Object
        if ObjectName:
            self._name_parser(ObjectName, attr_name)
        self.attr_name = attr_name

    def _name_parser(self, name, attr_name):
        if name.startswith('dict') or name.startswith('datetime') or name.startswith('str') \
                or name.startswith('int') or name.startswith('bool') or name.startswith('list[str]') \
                or name.startswith('object') or name.startswith('list[int]'):

            self.object = Leaves(name, attr_name)
            self.has_child_attr = False
        elif name.startswith('list['):
            name = name.split('list[')[1].split(']')[0]
            self.object = getattr(client, name)
            self.is_list_attr = True
        else:
            self.object = getattr(client, name)

    @property
    def name(self):
        return self.object.__name__

    def child_object(self, attr):
        return getattr(client, self.object.swagger_types[attr])()


@app.route('/node/<init_id>', methods=['post', 'get'])
def node(init_id):
    args = request.args.get('object_name').split('#')
    if args == ['', '']:
        version, attr_name = init_id.split('-')
        parent_name = getattr(KuberAPI, attr_name)[version]
        parent_attr = 'root'
    else:
        parent_name, attr_name, parent_attr = args

    print(request.args.get('object_name'), args)
    if not parent_name:
        parent_name = 'AppsV1beta1Deployment'
        attr_name = 'Deployment'
        parent_attr = 'root'
    attr = KuberParser(ObjectName=parent_name, attr_name=attr_name)
    res = {"id": attr.name + '#' + attr.attr_name + "#" + parent_attr, "text": attr.attr_name, 'children': []}
    for key, value in iteritems(attr.object.swagger_types):
        child = KuberParser(ObjectName=value, attr_name=attr.object.attribute_map[key])
        if child.has_child_attr:
            if child.is_list_attr:
                item = {"id": child.name + '#' + child.attr_name + ' | list' + '#' + attr.name, "text": child.attr_name + ' | list',
                        "children": child.has_child_attr}
            else:
                item = {"id": child.name + '#' + child.attr_name + '#' + attr.name, "text": child.attr_name,
                        "children": child.has_child_attr}
        else:
            item = {"id": child.name + '#' + child.attr_name + '#' + attr.name, "text": child.attr_name + ' | ' + child.name + '',
                    "type": 'leaf'}
        res['children'].append(item)
    return jsonify(res)


@app.route('/get_object')
def get_object():
    """
    return API objects
    :return:
    """
    obj = [i for i in KuberAPI.__dict__.keys() if not i.startswith('__')]
    return jsonify({'obj': obj})


@app.route('/get_version')
def get_version():
    """
    return API version
    :return:
    """
    obj = request.args.get('obj')
    if not obj:
        abort(400)
    obj = getattr(KuberAPI, obj)
    versions = [k for k, _ in iteritems(obj)]
    return jsonify({'versions': versions})


@app.route('/index')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0')

