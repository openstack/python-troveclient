from novaclient import base
from reddwarfclient.common import check_for_exceptions
import exceptions


class Database(base.Resource):
    """
    According to Wikipedia, "A database is a system intended to organize, store, and retrieve
    large amounts of data easily."
    """
    def __repr__(self):
        return "<Database: %s>" % self.name


class Databases(base.ManagerWithFind):
    """
    Manage :class:`Databases` resources.
    """
    resource_class = Database

    def create(self, instance_id, databases):
        """
        Create new databases within the specified instance
        """
        body = {"databases": databases}
        url = "/instances/%s/databases" % instance_id
        resp, body = self.api.client.post(url, body=body)
        check_for_exceptions(resp, body)

    def delete(self, instance_id, dbname):
        """Delete an existing database in the specified instance"""
        url = "/instances/%s/databases/%s" % (instance_id, dbname)
        resp, body = self.api.client.delete(url)
        check_for_exceptions(resp, body)

    def _list(self, url, response_key):
        resp, body = self.api.client.get(url)
        check_for_exceptions(resp, body)
        if not body:
            raise Exception("Call to " + url +
                            " did not return a body.")
        return [self.resource_class(self, res) for res in body[response_key]]

    def list(self, instance):
        """
        Get a list of all Databases from the instance.

        :rtype: list of :class:`Database`.
        """
        return self._list("/instances/%s/databases" % base.getid(instance),
                          "databases")

#    def get(self, instance, database):
#        """
#        Get a specific instances.
#
#        :param flavor: The ID of the :class:`Database` to get.
#        :rtype: :class:`Database`
#        """
#        assert isinstance(instance, Instance)
#        assert isinstance(database, (Database, int))
#        instance_id = base.getid(instance)
#        db_id = base.getid(database)
#        url = "/instances/%s/databases/%s" % (instance_id, db_id)
#        return self._get(url, "database")
