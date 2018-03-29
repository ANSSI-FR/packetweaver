import copy
import packetweaver.core.models.status as st


class AbilityInfo(object):
    def __init__(self, name,
                 description="",
                 authors=[],
                 references=[],
                 diffusion="",
                 tags=[],
                 reliability=st.Reliability.INCOMPLETE,
                 type=st.AbilityType.STANDALONE
                 ):
        """ Contains the information of an Ability

        :param name: name of the Ability, use to identify it in an ability package
        :param description: a description of the ability objectives
        :param authors: people involved in the writing.
        :param references: list of references containing: [a description, the date of
        visualisation/publication, information to find the resource]
        :param diffusion: a diffusion to tag abilities holding sensitive material
        :param tags: list of tags as defined in the class status.Tag
        :param reliability: same as tags, but to indicate how robust the ability is
        :param type: define if a module is standalone or a component. use status.AbilityType
        as well for predefined values
        """
        self._name = name
        self._description = description
        if isinstance(authors, str):
            self._authors = [authors]
        else:
            self._authors = copy.deepcopy(authors)
        self._refs = copy.deepcopy(references)
        self._diffusion = diffusion
        self._tags = copy.deepcopy(tags)
        self._reliability = reliability
        self._type = type

    def summary(self):
        """ Return a list of tuples containing the list of
        information that has been set """
        l = [
            ('name', self._name),
            ('type', str(self._type)),
        ]
        if len(self._description) > 0:
            l.append(('description', self._description))
        if len(self._authors) > 0:
            delimiter = '' if len(self._refs) == 1 else '\n- '
            l.append(('authors', delimiter + delimiter.join(self._authors)))
        if len(self._refs) > 0:
            delimiter = '' if len(self._refs) == 1 else '\n- '
            l.append(('references', delimiter + delimiter.join(['|'.join(x) for x in self._refs])))
        if len(self._diffusion) > 0:
            l.append(('diffusion', self._diffusion))
        if len(self._tags) > 0:
            l.append(('tags', ', '.join(self._tags)))
        if self._reliability is not None:
            l.append(('reliability', self._reliability))
        return l

    def get_name(self):
        return self._name

    def get_description(self):
        return self._description

    def get_tags(self):
        return copy.deepcopy(self._tags)

    def get_type(self):
        return self._type
