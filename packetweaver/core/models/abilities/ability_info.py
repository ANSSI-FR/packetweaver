import copy
import packetweaver.core.models.status as st


class AbilityInfo(object):
    def __init__(self, name,
                 description='',
                 authors=[],
                 references=[],
                 diffusion='',
                 tags=[],
                 reliability=st.Reliability.INCOMPLETE,
                 type=st.AbilityType.STANDALONE
                 ):
        """ Contains the information of an Ability

        :param name: the Ability name, to identify it in an ability package
        :param description: describes the ability objectives
        :param authors: list people involved in the writing
        :param references: list of references used for the writing or related
            to the ability. Its format is
            [a description, a validity date, a link to the resource]
        :param diffusion: a tag defining the sensitivity of the ability
        :param tags: list of tags as defined in the class status.Tag
        :param reliability: same as tag with status.Reliability
        :param type: define if a module is standalone or a component.
            See status.AbilityType for valid values.
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
        l_summary_items = [
            ('name', self._name),
            ('type', str(self._type)),
        ]
        if len(self._description) > 0:
            l_summary_items.append(('description', self._description))
        if len(self._authors) > 0:
            delimiter = '' if len(self._refs) == 1 else '\n- '
            l_summary_items.append(
                ('authors', delimiter + delimiter.join(self._authors))
            )
        if len(self._refs) > 0:
            delimiter = '' if len(self._refs) == 1 else '\n- '
            l_summary_items.append(
                ('references',
                 delimiter + delimiter.join(['|'.join(x) for x in self._refs]))
            )
        if len(self._diffusion) > 0:
            l_summary_items.append(('diffusion', self._diffusion))
        if len(self._tags) > 0:
            l_summary_items.append(('tags', ', '.join(self._tags)))
        if self._reliability is not None:
            l_summary_items.append(('reliability', self._reliability))
        return l_summary_items

    def get_name(self):
        return self._name

    def get_description(self):
        return self._description

    def get_tags(self):
        return copy.deepcopy(self._tags)

    def get_type(self):
        return self._type
