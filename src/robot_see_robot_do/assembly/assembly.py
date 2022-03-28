from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
from copy import deepcopy
from compas.geometry import Frame
from compas.geometry import Transformation, Translation
from compas.geometry import distance_point_point
from compas.datastructures import Network, network, mesh_offset
from compas_ghpython.artists import MeshArtist

import rhinoscriptsyntax as rs

from .element import Element

from .utilities import FromToData
from .utilities import FromToJson

__all__ = ['Assembly']


class Assembly(FromToData, FromToJson):
    """A data structure for discrete element assemblies.

    An assembly is essentially a network of assembly elements.
    Each element is represented by a node of the network.
    Each interface or connection between elements is represented by an edge of the network.

    Attributes
    ----------
    network : :class:`compas.Network`, optional
    elements : list of :class:`Element`, optional
        A list of assembly elements.
    attributes : dict, optional
        User-defined attributes of the assembly.
        Built-in attributes are:
        * name (str) : ``'Assembly'``
    default_element_attribute : dict, optional
        User-defined default attributes of the elements of the assembly.
        The built-in attributes are:
        * is_planned (bool) : ``False``
        * is_placed (bool) : ``False``
    default_connection_attributes : dict, optional
        User-defined default attributes of the connections of the assembly.

    Examples
    --------
    >>> assembly = Assembly()
    >>> for i in range(2):
    >>>     element = Element.from_box(Box(Frame.worldXY(), 10, 5, 2))
    >>>     assembly.add_element(element)
    """

    def __init__(self,
                 elements=None,
                 attributes=None,
                 default_element_attributes=None,
                 default_connection_attributes=None):

        self.network = Network()
        self.network.attributes.update({'name': 'Assembly'})

        if attributes is not None:
            self.network.attributes.update(attributes)

        self.network.default_node_attributes.update({
            'is_planned': False,
            'is_placed': False
        })

        if default_element_attributes is not None:
            self.network.default_node_attributes.update(default_element_attributes)

        if default_connection_attributes is not None:
            self.network.default_edge_attributes.update(default_connection_attributes)

        if elements:
            for element in elements:
                self.add_element(element)

    @property
    def name(self):
        """str : The name of the assembly."""
        return self.network.attributes.get('name', None)

    @name.setter
    def name(self, value):
        self.network.attributes['name'] = value

    def number_of_elements(self):
        """Compute the number of elements of the assembly.

        Returns
        -------
        int
            The number of elements.

        """
        return self.network.number_of_nodes()

    def number_of_connections(self):
        """Compute the number of connections of the assembly.

        Returns
        -------
        int
            the number of connections.

        """
        return self.network.number_of_edges()

    @property
    def data(self):
        """Return a data dictionary of the assembly.
        """
        # Network data does not recursively serialize to data...
        d = self.network.data

        # so we need to trigger that for elements stored in nodes
        node = {}
        for vkey, vdata in d['node'].items():
            node[vkey] = {key: vdata[key] for key in vdata.keys() if key != 'element'}
            node[vkey]['element'] = vdata['element'].to_data()

            if 'frame_est' in vdata:
                if node[vkey]['frame_est']:
                    node[vkey]['frame_est'] = node[vkey]['frame_est'].to_data()

        d['node'] = node

        return d

    @data.setter
    def data(self, data):
        # Deserialize elements from node dictionary
        for _vkey, vdata in data['node'].items():
            vdata['element'] = Element.from_data(vdata['element'])

            if 'frame_est' in vdata:
                if vdata['frame_est']:
                    vdata['frame_est'] = Frame.from_data(vdata['frame_est']) #node[vkey]['frame_est'].to_data()

        self.network = Network.from_data(data)

    def clear(self):
        """Clear all the assembly data."""
        self.network.clear()

    def add_element(self, element, key=None, attr_dict={}, **kwattr):
        """Add an element to the assembly.

        Parameters
        ----------
        element : Element
            The element to add.
        attr_dict : dict, optional
            A dictionary of element attributes. Default is ``None``.

        Returns
        -------
        hashable
            The identifier of the element.
        """
        attr_dict.update(kwattr)
        x, y, z = element.frame.point
        key = self.network.add_node(key=key, attr_dict=attr_dict,
                                    x=x, y=y, z=z, element=element)
        return key

    def add_element_(self, elem, current_key, direction=0, shift_value=0, placed_by='human', on_ground=False, module_index=0, frame_id=None, frame_est=None):
        """Add an element to the assembly.
        """
        N = self.network.number_of_nodes()

        new_elem_type = elem._type
        current_elem = self.network.node[current_key]['element']

        if direction == 0:
            current_connector = current_elem.connector_frame_2
        elif direction == 1:
            current_connector = current_elem.connector_frame_1

        if module_index == 0:
            connector_1_map = {0: False, 1:True}
            connector_2_map = {0: True, 1:False}
        elif module_index == 1:
            connector_1_map = {0: True, 1:True}
            connector_2_map = {0: True, 1:True}
        else:
            if new_elem_type == 'Z':
                connector_1_map = {0: True, 1:True}
                connector_2_map = {0: False, 1:False}
            else:
                connector_1_map = {0: True, 1:True}
                connector_2_map = {0: True, 1:True}
            if direction == 1:
                current_elem.connector_1_state = False
            else:
                current_elem.connector_2_state = False

        T = Transformation.from_frame_to_frame(Frame.worldXY(), current_connector)

        new_elem = elem.transformed(T)

        orient_map = {'X': current_elem._base_frame.xaxis, 'Y': current_elem._base_frame.yaxis, 'Z': current_elem._base_frame.zaxis}
        axis = orient_map[current_elem._type]
        if direction == 1:
            a = -1
        elif direction == 0:
            a = 1
        T = Translation.from_vector(axis*shift_value*a)

        new_elem.transform(T)

        new_elem.connector_1_state = connector_1_map[direction]
        new_elem.connector_2_state = connector_2_map[direction]

        #if self.collision_check(new_elem, tolerance = -0.001) == False:
        if True:
            self.add_element(new_elem, elem_type=new_elem_type, placed_by=placed_by, on_ground=on_ground, frame_id=frame_id, frame_est=frame_est)

            if module_index == 0:
                self.network.add_edge(current_key, N, edge_to='neighbour')
            elif module_index == 1:
                self.network.add_edge(N-1, N, edge_to='parent')
            else:
                self.network.add_edge(N-1, N, edge_to='parent')
                self.network.add_edge(N-2, N, edge_to='parent')

            self.check_open_connectors(new_elem, module_index)

        return new_elem


    def add_connection(self, u, v, attr_dict=None, **kwattr):
        """Add a connection between two elements and specify its attributes.

        Parameters
        ----------
        u : hashable
            The identifier of the first element of the connection.
        v : hashable
            The identifier of the second element of the connection.
        attr_dict : dict, optional
            A dictionary of connection attributes.
        kwattr
            Other connection attributes as additional keyword arguments.

        Returns
        -------
        tuple
            The identifiers of the elements.
        """
        return self.network.add_edge(u, v, attr_dict, **kwattr)

    def add_joint(self, edge, joint):
        """
        """
        u, v = edge
        return self.add_edge(u, v, joint=joint)

    def transform(self, transformation):
        """Transforms this assembly.

        Parameters
        ----------
        transformation : :class:`Transformation`

        Returns
        -------
        None
        """
        for _k, element in self.elements(data=False):
            element.transform(transformation)

    def transformed(self, transformation):
        """Returns a transformed copy of this assembly.

        Parameters
        ----------
        transformation : :class:`Transformation`

        Returns
        -------
        Assembly
        """
        assembly = self.copy()
        assembly.transform(transformation)
        assembly.network.transform(transformation)
        return assembly

    def copy(self):
        """Returns a copy of this assembly.
        """
        cls = type(self)
        return cls.from_data(deepcopy(self.data))

    def element(self, key, data=False):
        """Get an element by its key."""
        if data:
            return self.network.node[key]['element'], self.network.node[key]
        else:
            return self.network.node[key]['element']

    def elements(self, data=False):
        """Iterate over the elements of the assembly.

        Parameters
        ----------
        data : bool, optional
            If ``True``, yield both the identifier and the attributes.

        Yields
        ------
        2-tuple
            The next element as a (key, element) tuple, if ``data`` is ``False``.
        3-tuple
            The next element as a (key, element, attr) tuple, if ``data`` is ``True``.

        """
        if data:
            for vkey, vattr in self.network.nodes(True):
                yield vkey, vattr['element'], vattr
        else:
            for vkey in self.network.nodes(data):
                yield vkey, self.network.node[vkey]['element']

    def connections(self, data=False):
        """Iterate over the connections of the network.

        Parameters
        ----------
        data : bool, optional
            If ``True``, yield both the identifier and the attributes.

        Yields
        ------
        2-tuple
            The next connection identifier (u, v), if ``data`` is ``False``.
        3-tuple
            The next connection as a (u, v, attr) tuple, if ``data`` is ``True``.

        """
        return self.network.edges(data)

    def direction(self, current_key, current_connector_key):
        """Compute direction of growth.
        """
        current_elem = self.network.node[current_key]['element']
        current_elem_type = current_elem._type
        current_connectors = current_elem.connectors(state='open')

        orient_map = {'X': 0, 'Y': 1, 'Z': 2}
        axis = orient_map[current_elem_type]

        current_location = current_elem.tool_frame.point[axis]

        if current_connectors:
            next_location = current_connectors[current_connector_key].point[axis]
            if current_location > next_location:
                direction = 0
            else:
                direction = 1
            return direction

    def sequence(self, start_type, on_ground=False):
        """Compute the sequence for element placement.
        """
        sequence = []

        if start_type == 'X':
            sequence = ['X', 'Y', 'Z']
        if start_type == 'Y' and on_ground:
            sequence = ['X', 'Y', 'Z']
        else:
            sequence = ['X', 'Y', 'Z']  # should be Y,X,Z when on ground=False
        if start_type == 'Z':
            sequence = ['Z', 'X', 'Y']

        return sequence

    def collision_check(self, elem, tolerance):
        """Check for collisions with assembly elements.
        """

        #key_index = self.network.key_index()
        #keys = [key_index[key] for key in self.network.nodes()]
        keys = [key for key, element in self.elements()]
        elements = [self.element(key) for key in keys]

        collision = False

        for element in elements:
            elem_mesh_offset = mesh_offset(elem.mesh, distance=tolerance, cls=None)

            artist1 = MeshArtist(elem_mesh_offset)
            elem_rmesh = artist1.draw_mesh()

            artist2 = MeshArtist(element.mesh)
            assembly_rmesh = artist2.draw_mesh()

            results = rs.MeshMeshIntersection(elem_rmesh, assembly_rmesh)
            if results:
                collision = True

        return collision

    def add_module(self, elem_x, elem_y, elem_z, current_key, direction=0, shift_value=0, on_ground=False, added_frame_id=None, frame_est=None):
        """Add a module to the assembly.
        """
        type_map = {'X': elem_x, 'Y': elem_y, 'Z': elem_z}
        current_elem_type = self.network.node[current_key]['elem_type']
        sequence = self.sequence(current_elem_type)

        keys_robot = []

        for i, s in enumerate(sequence):
            if i != 0:
                placed_by = 'robot'
                frame_id = None
                my_new_elem = self.add_element_(type_map[s], current_key, direction=direction, shift_value=shift_value, placed_by=placed_by, on_ground=False, module_index=i, frame_id=frame_id, frame_est=None)
                keys_robot += list(self.network.nodes_where({'element': my_new_elem}))
            else:
                placed_by = 'human'
                frame_id = added_frame_id
                my_new_elem = self.add_element_(type_map[s], current_key, direction=direction, shift_value=shift_value, placed_by=placed_by, on_ground=False, module_index=i, frame_id=frame_id, frame_est=frame_est)
                keys_human = list((self.network.nodes_where({'element': my_new_elem})))

        keys_dict = {'keys_human': keys_human, 'keys_robot':keys_robot}

        return keys_dict

    def parent_key(self, point, within_dist):
        """Return the parent key of a tracked object.
        """
        parent_key = None

        for key, element in self.elements():
            connectors = element.connectors(state='open')
            for connector in connectors:
                dist = distance_point_point(point, connector.point)
                if dist < within_dist:
                    parent_key = key

        return parent_key


    def check_open_connectors(self, my_new_elem, module_index):

        # TO DO: get elems in defined distance (maybe useful: # geometric keys)
        #key_index = self.network.key_index()
        #keys = [key_index[key] for key in self.network.nodes()]
        keys = [key for key, element in self.elements()]
        new_keys = keys[:-1]

        for key in new_keys:
            sel_element = self.network.node[key]['element']
            elem_connectors = self.element(key).connectors(state='open')
            for i, connector in enumerate(elem_connectors):
                if my_new_elem._base_frame == connector and module_index == 2:
                    if len(elem_connectors) == 2:
                        if i == 0:
                            sel_element.connector_1_state = False
                            my_new_elem.connector_2_state = False
                        elif i == 1:
                            sel_element.connector_2_state = False
                            my_new_elem.connector_1_state = False
                    elif len(elem_connectors) == 1:
                        if sel_element.connector_1_state == False:
                            sel_element.connector_2_state = False
                            my_new_elem.connector_1_state = False
                        elif sel_element.connector_2_state == False:
                            sel_element.connector_1_state = False
                            my_new_elem.connector_2_state = False

    def keys_within_radius(self, current_key):

        for key, element in self.elements(data=True):
            pass

    def keys_within_radius_xy(self, current_key):
        pass

    def keys_within_radius_domain(self, current_key):
        pass

    def range_filter(self, base_frame):
        """Disable connectors outside of a given range, e.g. robot reach.
        """
        ur_range_max = 1.3
        ur_range_min = 0.75

        for key, element in self.elements():
            if element.connector_1_state == True:
                distance = distance_point_point(element.connector_frame_1.point, base_frame.point)
                if not ur_range_min <= distance <= ur_range_max:
                    element.connector_1_state = False
            elif element.connector_2_state == True:
                distance = distance_point_point(element.connector_frame_2.point, base_frame.point)
                if not ur_range_min <= distance <= ur_range_max:
                    element.connector_2_state = False
            else:
                pass

    def options_elements(self, elem_x, elem_y, elem_z):
        """Returns a list of elements.
        """
        keys = [key for key, element in self.elements()]
        return [self.element(key).options_elements(elem_x=elem_x, elem_y=elem_y, elem_z=elem_z) for key in keys]


    def options_vectors(self):
        """Returns a list of vectors.
        """
        keys = [key for key, element in self.elements()]
        return [self.element(key).options_vectors() for key in keys]


    def connectors(self, state='all'):
        """ Get assembly's connectors.

        Parameters
        ----------
        state : string
            A string indentifying the connectors' state.

        'all' : return all connectors.
        'open' : return all open connectors.
        'closed' : return all closed connectors.

        Returns
        -------
        list
            A list of frames.

        """
        #key_index = self.network.key_index()
        #keys = [key_index[key] for key in self.network.nodes()]
        keys = [key for key, element in self.elements()]
        return [self.element(key).connectors(state) for key in keys]


    def export_building_plan(self):
        """
        exports the building plan by using the following protocol:

        the first lines are the description of the global markers (fixed in the world frame):
        type [string], element pose [6]
        = "GM", x, y, z, qw, qx, qy, qz

        the next lines contain the wall information:
        type [string], element pose [6], string_message [string]
        = type, x, y, z, qw, qx, qy, qz, string_message
        """

        print("exporting")
        building_plan = []

        for key, element, data in self.elements(data=True):
            line = []

            t = element._type
            line.append(t) #type
            line += element.get_pose_quaternion() #element pose
            string_message = "This is the element with the key index %i" %key
            line.append(string_message)
            building_plan.append(line)

        print(building_plan)
        exporter = Exporter()
        exporter.delete_file()
        exporter.export_building_plan(building_plan)

    def export_to_json_for_xr(self, path, is_built=False):

        self.network.update_default_node_attributes({"is_built":False,"idx_v":None,"custom_attr_1":None,"custom_attr_2":None,"custom_attr_3":None})

        for key, element in self.elements():
            idx_v = self.network.node_attribute(key, "course")
            self.network.node_attribute(key, "idx_v", idx_v)
            self.network.node_attribute(key, "is_built", is_built)

        self.to_json(path)
