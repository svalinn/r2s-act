import itertools
from collections import namedtuple

from itaps import iBase, iMesh, iMeshExtensions


class ScdMeshError(Exception):
    pass


class ScdMesh:
    """A structured mesh in the spirit of MOAB's ScdMesh interface."""

    # A six-element tuple corresponding to the BOX_DIMS tag on the
    # structured mesh.  See the MOAB library's metadata-info.doc file.
    extents_tuple = namedtuple('extents',
                               ('imin', 'jmin', 'kmin',
                                'imax', 'jmax', 'kmax'))

    def __init__(self, mesh, x_points, y_points, z_points, **kw):
        """Construct a ScdMesh from given x, y, and z coordinates

           The i,j,k extents of the structured mesh will be numbered from 0.

           keyword arguments:
           bdtag = if the BOX_DIMS tag has already been looked up, it may
                   be passed thus
           _scdset = an existing scdset to use; users should use fromEntSet
        """
        self.mesh = mesh
        if x_points is None and y_points is None and z_points is None:
            self.scdset = kw['_scdset']
        else:
            extents = [0, 0, 0]
            extents.extend([len(x) for x in [x_points, y_points, z_points]])
            self.scdset = mesh.createStructuredMesh(
                    extents, i=x_points, j=y_points, k=z_points,
                    create_set=True)
        bdtag = kw.get('bdtag', mesh.getTagHandle('BOX_DIMS'))
        self.dims = ScdMesh.extents_tuple(*bdtag[self.scdset])
        vdims_incr = list(self.dims[0:3]) + [x + 1 for x in self.dims[3:6]]
        self.vdims = ScdMesh.extents_tuple(*vdims_incr)
        # Our access iterators must have size=2 for now, until iMesh non-array
        # iterators receive support for the stepIter function
        self.hexit = self.scdset.iterate(iBase.Type.region,
                                         iMesh.Topology.hexahedron, size=2)
        self.vtxit = self.scdset.iterate(iBase.Type.vertex,
                                         iMesh.Topology.point, size=2)

    @classmethod
    def fromFile(cls, mesh, filename):
        """Load structured meshes from a file

        Returns one strutured mesh if the file contains one mesh, or a list if
        the file contains multiple meshes.
        """
        retlist = []
        mesh.rootSet.load(filename)
        bdtag = mesh.getTagHandle('BOX_DIMS')
        for eset in mesh.rootSet.getEntSets():
            try:
                bdtag[eset]
                retlist.append(ScdMesh(mesh, None, None, None,
                                       _scdset=eset, bdtag=bdtag))
            except iBase.TagNotFoundError:
                pass
        if len(retlist) == 1:
            return retlist[0]
        else:
            return retlist

    @classmethod
    def fromEntSet(cls, mesh, eset):
        """Constructor function: create a ScdMesh from an existing entity set

        The eset parameter must be a structured mesh set with the BOX_DIMS
        tag set on it.
        """
        m = ScdMesh(mesh, None, None, None, _scdset=eset)
        return m

    @staticmethod
    def _dimConvert(dims, ijk):
        """Helper method fo getVtx and getHex

        For tuple (i,j,k), return the number N in the appropriate iterator.
        """
        dim0 = [0] * 3
        for i in xrange(0, 3):
            if (dims[i] > ijk[i] or dims[i + 3] <= ijk[i]):
                raise ScdMeshError(str(ijk) + ' is out of bounds')
            dim0[i] = ijk[i] - dims[i]
        i0, j0, k0 = dim0
        n = (((dims[4] - dims[1]) * (dims[3] - dims[0]) * k0) +
             ((dims[3] - dims[0]) * j0) +
             i0)
        return n

    @staticmethod
    def _stepIter(it, n):
        """Helper method for getVtx and getHex

        Return the nth item in the iterator"""
        it.step(n)
        r = it.next()[0]
        it.reset()
        return r

    def getVtx(self, i, j, k):
        """Return the (i,j,k)'th vertex in the mesh"""
        n = ScdMesh._dimConvert(self.vdims, (i, j, k))
        return ScdMesh._stepIter(self.vtxit, n)

    def getHex(self, i, j, k):
        """Return the (i,j,k)'th hexahedron in the mesh"""
        n = ScdMesh._dimConvert(self.dims, (i, j, k))
        return ScdMesh._stepIter(self.hexit, n)

    def iterateHex(self, order='xyz', **kw):

        # a valid order has the letters 'x', 'y', and 'z'
        # in any order without duplicates
        if not (len(order) <= 3 and
                len(set(order)) == len(order) and
                all([a in 'xyz' for a in order])):
            raise ScdMeshError('Invalid iteration order: ' + str(order))

        # special case: xyz order is the standard pytaps iteration order,
        # so we can save time by simply returning a pytaps iterator
        # FIXME: can't use this unless kw are emptyh
        #if order == 'xyz':
        #    self.scdset.iterate(iBase.Type.region, iMesh.Topology.hexahedron)
        #    return

        indices = []
        for L in order:
            idx = 'xyz'.find(L)
            indices.append(kw.get(L, range(self.dims[idx], self.dims[idx+3])))
            if isinstance( indices[-1], int ):
                indices[-1] = [indices[-1]]

        print indices
        indices[0], indices[2] = indices[2], indices[0]

        items = itertools.product(*(indices))

        ordmap = [order.find(L) for L in 'xyz']

        for i in items:
            i = list(i)
            i[0], i[2] = i[2], i[0]
            item = [i[x] for x in ordmap]
            yield self.getHex(*item)
