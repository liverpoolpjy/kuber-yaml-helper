from kubernetes import client
from flask import Flask, render_template, request, jsonify
from six import iteritems

app = Flask(__name__)


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
                or name.startswith('object'):
            # self.object = name
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


@app.route('/node/', methods=['post', 'get'])
def node():
    args = request.args.get('object_name').split('#')
    print(request.args.get('object_name'), args)
    parent_name = args[0]
    # attr_name = request.args.get('attr_name')
    attr_name = args[1]
    parent_attr = args[-1]
    if not parent_name:
        parent_name = 'AppsV1beta1Deployment'
        attr_name = 'Deployment'
        parent_attr = 'root'
    attr = KuberParser(ObjectName=parent_name, attr_name=attr_name)
    res = {"id": attr.name + '#' + attr.attr_name + "#" + parent_attr, "text": attr.attr_name, 'children': []}
    for key, value in iteritems(attr.object.swagger_types):
        child = KuberParser(ObjectName=value, attr_name=attr.object.attribute_map[key])
        if child.has_child_attr:
            item = {"id": child.name + '#' + child.attr_name + '#' + attr.name, "text": child.attr_name,
                    "children": child.has_child_attr}
        else:
            item = {"id": child.name + '#' + child.attr_name + '#' + attr.name, "text": child.attr_name + ' ' + child.name,
                    "type": 'leaf'}
        res['children'].append(item)
    return jsonify(res)


@app.route('/index')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0')

