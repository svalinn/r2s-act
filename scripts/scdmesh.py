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

    def iterateHex(self, order='zyx', **kw):
        """Get an iterator over the hexahedra of the mesh

        The order argument specifies the iteration order.  It must be a string
        of 1-3 letters from the set (x,y,z).  The rightmost letter is the axis
        along which the iteration will advance the most quickly.  Thus 'zyx' --
        x coordinates changing fastest, z coordinates changing least fast-- is
        the default, and is identical to the order that would be given by the
        scdset.iterate() function.

        When a dimension is absent from the order, iteration will proceed over
        only the column in the mesh that has the lowest corresonding (i/j/k)
        coordinate.  Thus, with order 'xy,' iteration proceeds over the i/j
        plane of the structured mesh with the smallest k coordinate.

        Specific slices can be specified with keyword arguments:

        Keyword args:
          x: specify one or more i-coordinates to iterate over.
          y: specify one or more j-coordinates to iterate over.
          z: specify one or more k-coordinates to iterate over.

        Examples:
          iterateHex(): equivalent to iMesh iterator over hexes in mesh
          iterateHex( 'xyz' ): iterate over entire mesh, with k-coordinates
                               changing fastest, i-coordinates least fast.
          iterateHex( 'yz', x=3 ): Iterate over the j-k plane of the mesh
                                   whose i-coordinate is 3, with k values
                                   changing fastest.
          iterateHex( 'z' ): Iterate over k-coordinates, with i=dims.imin
                             and j=dims.jmin
          iterateHex( 'yxz', y=(3,4) ): Iterate over all hexes with
                                        j-coordinate = 3 or 4.  k-coordinate
                                        values change fastest, j-values least
                                        fast.

        Performance:
          This function is currently very slow for large meshes, except when
          order=zyx and  no kwargs are specified.  Improving performance
          is an active area of development.
        """

        # a valid order has the letters 'x', 'y', and 'z'
        # in any order without duplicates
        if not (len(order) <= 3 and
                len(set(order)) == len(order) and
                all([a in 'xyz' for a in order])):
            raise ScdMeshError('Invalid iteration order: ' + str(order))

        # special case: zyx order is the standard pytaps iteration order,
        # so we can save time by simply returning a pytaps iterator
        # if no kwargs were specified
        if order == 'zyx' and not kw:
            return self.scdset.iterate(iBase.Type.region, iMesh.Topology.hexahedron)

        # process kw
        spec = {}
        for idx, d in enumerate('xyz'):
            if d in kw:
                spec[d] = kw[d]
                if isinstance(spec[d], int):
                    spec[d] = [spec[d]]
                if not all(x in range(self.dims[idx], self.dims[idx+3])
                           for x in spec[d]):
                    raise ScdMeshError('Invalid iterator kwarg: ' + str(spec[d]))
                if d not in order and len(spec[d]) > 1:
                    raise ScdMeshError('Cannot iterate over' + str(spec[d]) +
                                       'without a proper iteration order')
            if d not in order:
                order = d+order
                spec[d] = spec.get(d, [self.dims[idx]])

        indices = []
        for L in order:
            idx = 'xyz'.find(L)
            indices.append(spec.get(L, xrange(self.dims[idx], self.dims[idx+3])))

        items = itertools.product(*(indices))
        ordmap = [order.find(L) for L in 'xyz']

        def it(items, ordmap):
            dy = (self.dims[3]-self.dims[0])
            dz = (self.dims[4]-self.dims[1]) * dy
            it = self.hexit
            for i in items:
                #n = sum( d*x for d,x in zip( (dz,dy,1), [i[f] for f in ordmap] ) )
                n = dz*i[ordmap[2]] + dy*i[ordmap[1]] + i[ordmap[0]]
                it.step(n)
                r = it.next()[0]
                it.reset()
                yield r

        return it(items, ordmap)
