# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

urns_query = """query ($offset: Int) {
      allUrns(first: 5000, offset: $offset) {
        nodes {
          urnIdentifier
          ilkIdentifier
          ink
          art
        }
      }
    }"""

ilks_query = """query {
      allIlks(first: 100) {
        nodes {
          id
          spot
          rate
          mat
          chop
        }
      }
    }"""