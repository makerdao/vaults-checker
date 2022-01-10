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

import argparse
import logging
import sys
import requests
import json

from vaults_checker.queries import ilks_query, urns_query

from pprint import pformat
from web3 import Web3, HTTPProvider
from pymaker.deployment import DssDeployment, Ray, Wad


class VaultsChecker:
    """VaultsChecker."""

    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog='vaults-checker')

        parser.add_argument("--rpc-url", type=str, required=True,
                            help="JSON-RPC host URL")

        parser.add_argument("--rpc-timeout", type=int, default=10,
                            help="JSON-RPC timeout (in seconds, default: 10)")

        parser.add_argument("--ilk", type=str,
                            help="ILK to query")

        parser.add_argument('--target-price', type=float,
                            help="Target price for given ILK")

        self.arguments = parser.parse_args(args)

    def main(self):
        provider = HTTPProvider(endpoint_uri='https://parity1.mainnet.makerops.services/rpc',
                                request_kwargs={'timeout': 23})
        web3: Web3 = Web3(provider)
        mcd = DssDeployment.from_node(web3)
        for collateral, info in get_data(mcd, self.arguments.ilk, self.arguments.target_price,).items():
            print("====================================================")
            print(f"Collateral: {collateral} \n"
                  f"Current OSM price: {info.osm_price} | Next OSM price: {info.next_osm_price} | Target price: {info.target_price} \n"
                  f"Total collateral to liquidate: {info.total_collateral} | Total DAI to liquidate: {info.dai_required}")
            print("====================================================")
            print("Vaults at risk: \n")
            for urn in info.risky_urns:
                print(f"URN: {urn.identifier} | Liquidation Price: {urn.liquidation_price} | Collateral: {urn.ink}")
            print("====================================================")


class Urn:
    def __init__(self, identifier: str, ink: Wad, art: Wad, spot: Ray, mat: Ray, rate: Ray):
        assert isinstance(identifier, str)
        assert isinstance(ink, Wad)
        assert isinstance(art, Wad)
        assert isinstance(spot, Ray)
        assert isinstance(mat, Ray)
        assert isinstance(rate, Ray)

        self.identifier = identifier
        self.ink = float(ink)
        self.art = float(art)
        if self.art > 0 and rate > Ray(0):
            debt = Ray(art) * rate
            self.liquidation_price = float(debt * mat / Ray(ink))
            osm_price = spot * mat
            self.collateralization = float(Ray(ink) * osm_price / debt)
            self.safe = Ray(ink) * spot >= debt
        else:
            self.liquidation_price = None
            self.collateralization = None
            self.safe = True

    def __repr__(self):
        return pformat(vars(self))


class Collateral:
    def __init__(self, osm_price, next_osm_price, target_price, total_collateral, dai_required, risky_urns):
        assert isinstance(osm_price, float)
        assert isinstance(next_osm_price, float)
        assert isinstance(target_price, float)
        assert isinstance(total_collateral, float)
        assert isinstance(dai_required, float)

        self.osm_price = osm_price
        self.next_osm_price = next_osm_price
        self.target_price = target_price
        self.total_collateral = total_collateral
        self.dai_required = dai_required
        self.risky_urns = risky_urns


def run_query(query: str, variables=None):
    assert isinstance(query, str)
    assert isinstance(variables, dict) or variables is None

    if variables:
        body = {'query': query, 'variables': json.dumps(variables)}
    else:
        body = {'query': query}
    response = requests.post('https://api.makerdao.com/graphql', json=body, timeout=30)
    if not response.ok:
        error_msg = f"{response.status_code} {response.reason} ({response.text})"
        raise RuntimeError(f"Vulcanize query failed: {error_msg}")
    return response


def get_data(mcd: DssDeployment, ilk: str, target_price: float):
    assert isinstance(mcd, DssDeployment)

    # Query ilks
    ilk_response = run_query(query=ilks_query)
    ilk_data = json.loads(ilk_response.text)['data']

    # Query urn state
    nodes = []
    data_needed = True
    page_size = 5000
    offset = 0
    while data_needed:
        urn_response = run_query(query=urns_query, variables={'offset': offset})
        result = json.loads(urn_response.text)
        if len(result['data']['allUrns']['nodes']) > 0:  # There are more results to add
            nodes += result['data']['allUrns']['nodes']
            offset += page_size
        else:  # No more results were returned, assume we read all the records
            data_needed = False

    vdb_data = {**ilk_data, 'allUrns': {'nodes': nodes}}

    data = {}

    if ilk is not None:
        get_collateral_data(mcd, vdb_data, data, target_price, ilk)
    else:
        for collateral in mcd.collaterals:
            get_collateral_data(mcd, vdb_data, data, target_price, collateral)

    return data


def get_collateral_data(mcd, vdb_data, data, target_price, collateral: str):
    osm_price = float(mcd.collaterals[collateral].pip.peek())
    next_osm_price = float(mcd.collaterals[collateral].pip.peep())

    if target_price is None:
        target_price = next_osm_price

    data[collateral] = Collateral(osm_price=osm_price, next_osm_price=next_osm_price, target_price=target_price,
                                  total_collateral=0.0, dai_required=0.0, risky_urns=[])

    ilk_nodes = filter(lambda node: node['id'] == collateral, vdb_data['allIlks']['nodes'])

    for ilk_node in ilk_nodes:
        dai_required = 0.0
        total_collateral = 0.0

        if ilk_node['spot'] and ilk_node['mat'] and ilk_node['rate']:
            spot = Ray(int(ilk_node['spot']))
            mat = Ray(int(ilk_node['mat']))
            rate = Ray(int(ilk_node['rate']))
            chop = Wad(int(ilk_node['chop'])) if ilk_node['chop'] else 1
            urn_nodes = filter(lambda urn_node: urn_node['ilkIdentifier'] == collateral, vdb_data['allUrns']['nodes'])
            urns_for_ilk = []

            for urn_node in urn_nodes:
                try:
                    identifier = urn_node['urnIdentifier']
                    ink = Wad(int(urn_node['ink']))
                    art = Wad(int(urn_node['art']))
                    urns_for_ilk.append(Urn(identifier, ink, art, spot, mat, rate))
                except (ArithmeticError, TypeError):
                    logging.error(f"Could not process {urn_node}")

            urns_with_art = list(filter(lambda urn: urn.art > 0, urns_for_ilk))
            risky_urns = sorted(filter(lambda urn: urn.liquidation_price > float(target_price), urns_with_art),
                                key=lambda urn: urn.collateralization)

            if risky_urns:
                dai_required = sum(risky_urn.art for risky_urn in risky_urns) * float(rate) * float(chop)
                total_collateral = sum(risky_urn.ink for risky_urn in risky_urns)

            data[collateral] = Collateral(osm_price=osm_price, next_osm_price=next_osm_price, target_price=target_price,
                                          total_collateral=total_collateral, dai_required=dai_required,
                                          risky_urns=risky_urns)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
    VaultsChecker(sys.argv[1:]).main()
