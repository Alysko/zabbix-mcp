"""Tests for zabbix_mcp.tools.host — host_get and host_interface_get."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from zabbix_mcp.tools.host import zabbix_host_get, zabbix_host_interface_get
from zabbix_mcp.errors import ZabbixAuthError


def _mock_client(return_value: object):
    mock = AsyncMock()
    mock.call = AsyncMock(return_value=return_value)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.host.ZabbixClient", return_value=cm)


class TestZabbixHostGet:
    async def test_returns_hosts(self, zabbix_env: dict) -> None:
        expected = [{"hostid": "1", "host": "server1", "name": "Server 1", "status": "0"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_host_get()
        assert result == expected

    async def test_default_params(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get()
        mock.call.assert_awaited_once_with("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "limit": 100,
        })

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(hostids=["1", "2"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["1", "2"]

    async def test_filter_by_groupids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(groupids=["5"])
        params = mock.call.call_args[0][1]
        assert params["groupids"] == ["5"]

    async def test_filter_by_templateids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(templateids=["10"])
        params = mock.call.call_args[0][1]
        assert params["templateids"] == ["10"]

    async def test_filter_by_status(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(status=0)
        params = mock.call.call_args[0][1]
        assert params["filter"] == {"status": 0}

    async def test_search_by_name(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(name="web")
        params = mock.call.call_args[0][1]
        assert params["search"] == {"name": "web"}

    async def test_custom_limit(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(limit=50)
        params = mock.call.call_args[0][1]
        assert params["limit"] == 50

    async def test_custom_output(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_get(output=["hostid", "host", "interfaces"])
        params = mock.call.call_args[0][1]
        assert params["output"] == ["hostid", "host", "interfaces"]

    async def test_empty_results(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            result = await zabbix_host_get()
        assert result == []

    async def test_propagates_auth_error(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client(None)
        mock.call.side_effect = ZabbixAuthError("Not authorized")
        with ctx:
            with pytest.raises(ZabbixAuthError):
                await zabbix_host_get()


class TestZabbixHostInterfaceGet:
    async def test_returns_interfaces(self, zabbix_env: dict) -> None:
        expected = [{"interfaceid": "1", "hostid": "1", "ip": "192.168.1.10", "port": "10050"}]
        mock, ctx = _mock_client(expected)
        with ctx:
            result = await zabbix_host_interface_get(hostids=["1"])
        assert result == expected

    async def test_calls_correct_method(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get()
        assert mock.call.call_args[0][0] == "hostinterface.get"

    async def test_filter_by_hostids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get(hostids=["1", "2"])
        params = mock.call.call_args[0][1]
        assert params["hostids"] == ["1", "2"]

    async def test_filter_by_type(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get(type=2)
        params = mock.call.call_args[0][1]
        assert params["filter"] == {"type": 2}

    async def test_filter_by_interfaceids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client([])
        with ctx:
            await zabbix_host_interface_get(interfaceids=["10"])
        params = mock.call.call_args[0][1]
        assert params["interfaceids"] == ["10"]


from zabbix_mcp.tools.host import (  # noqa: E402
    zabbix_host_create,
    zabbix_host_update,
    zabbix_host_interface_create,
    zabbix_host_interface_update,
)


class TestZabbixHostCreate:
    async def test_calls_host_create(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostids": ["10"]})
        with ctx:
            result = await zabbix_host_create(
                host="web-server-01",
                groups=[{"groupid": "2"}],
                interfaces=[{"type": 1, "main": 1, "useip": 1, "ip": "192.168.1.10", "dns": "", "port": "10050"}],
            )
        assert mock.call.call_args[0][0] == "host.create"
        assert result == {"hostids": ["10"]}

    async def test_required_params_sent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        iface = [{"type": 1, "main": 1, "useip": 1, "ip": "10.0.0.1", "dns": "", "port": "10050"}]
        with ctx:
            await zabbix_host_create(host="h", groups=[{"groupid": "1"}], interfaces=iface)
        params = mock.call.call_args[0][1]
        assert params["host"] == "h"
        assert params["groups"] == [{"groupid": "1"}]
        assert params["interfaces"] == iface

    async def test_optional_templates(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_create(
                host="h", groups=[{"groupid": "1"}],
                templates=[{"templateid": "10"}],
            )
        assert mock.call.call_args[0][1]["templates"] == [{"templateid": "10"}]

    async def test_default_status_enabled(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_create(host="h", groups=[{"groupid": "1"}])
        assert mock.call.call_args[0][1]["status"] == 0

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_create(host="h", groups=[{"groupid": "1"}])
        params = mock.call.call_args[0][1]
        assert "interfaces" not in params
        assert "templates" not in params
        assert "inventory_mode" not in params


class TestZabbixHostUpdate:
    async def test_calls_host_update(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostids": ["10"]})
        with ctx:
            result = await zabbix_host_update(hostid="10", status=1)
        assert mock.call.call_args[0][0] == "host.update"
        assert result == {"hostids": ["10"]}

    async def test_sends_hostid(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_update(hostid="42")
        assert mock.call.call_args[0][1]["hostid"] == "42"

    async def test_none_fields_absent(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_update(hostid="1")
        params = mock.call.call_args[0][1]
        assert "host" not in params
        assert "templates" not in params
        assert "status" not in params


def _mock_client_seq(*returns: object):
    """Mock client whose successive .call() invocations return the given values."""
    mock = AsyncMock()
    mock.call = AsyncMock(side_effect=list(returns))
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=mock)
    cm.__aexit__ = AsyncMock(return_value=None)
    return mock, patch("zabbix_mcp.tools.host.ZabbixClient", return_value=cm)


_AGENT_IF = {
    "interfaceid": "5", "hostid": "10", "type": "1", "main": "1", "useip": "1",
    "ip": "192.168.1.1", "dns": "", "port": "10050", "details": [],
    "available": "1", "error": "", "errors_from": "0", "disable_until": "0",
}
_SNMP_IF = {
    "interfaceid": "6", "hostid": "10", "type": "2", "main": "1", "useip": "1",
    "ip": "192.168.1.1", "dns": "", "port": "161",
    "details": {"version": "3", "bulk": "1", "securityname": "zbx"},
    "available": "1", "error": "", "errors_from": "0", "disable_until": "0",
}
_READ_ONLY = ("available", "error", "errors_from", "disable_until", "hostid")


class TestZabbixHostInterfaceCreate:
    async def test_uses_host_update_not_hostinterface_create(self, zabbix_env: dict) -> None:
        new_if = {**_AGENT_IF, "interfaceid": "7", "main": "0", "ip": "1.2.3.4"}
        mock, ctx = _mock_client_seq(
            [{"hostid": "10", "interfaces": [_AGENT_IF]}],
            {"hostids": ["10"]},
            [{"hostid": "10", "interfaces": [_AGENT_IF, new_if]}],
        )
        with ctx:
            result = await zabbix_host_interface_create(
                hostid="10", type=1, main=0, useip=1, ip="1.2.3.4", dns="", port="10050",
            )
        methods = [c.args[0] for c in mock.call.call_args_list]
        assert methods == ["host.get", "host.update", "host.get"]
        assert "hostinterface.create" not in methods
        assert result == {"interfaceids": ["7"]}

    async def test_existing_interfaces_kept_with_ids(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_seq(
            [{"hostid": "10", "interfaces": [_AGENT_IF, _SNMP_IF]}],
            {"hostids": ["10"]},
            [{"hostid": "10", "interfaces": [_AGENT_IF, _SNMP_IF]}],
        )
        with ctx:
            await zabbix_host_interface_create(
                hostid="10", type=1, main=0, useip=1, ip="1.2.3.4", dns="", port="10050",
            )
        params = mock.call.call_args_list[1].args[1]
        assert params["hostid"] == "10"
        ifaces = params["interfaces"]
        assert [i.get("interfaceid") for i in ifaces] == ["5", "6", None]
        assert ifaces[2]["ip"] == "1.2.3.4"
        for iface in ifaces:
            for field in _READ_ONLY:
                assert field not in iface
        assert "details" not in ifaces[0]          # agent interface: no details
        assert ifaces[1]["details"] == _SNMP_IF["details"]

    async def test_unknown_host_raises(self, zabbix_env: dict) -> None:
        from zabbix_mcp.errors import ZabbixNotFoundError
        mock, ctx = _mock_client_seq([])
        with ctx, pytest.raises(ZabbixNotFoundError):
            await zabbix_host_interface_create(
                hostid="999", type=1, main=1, useip=1, ip="1.2.3.4", dns="", port="10050",
            )
        assert mock.call.call_count == 1


class TestZabbixHostInterfaceUpdate:
    async def test_uses_host_update_with_merged_change(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_seq(
            [{"interfaceid": "6", "hostid": "10"}],
            [{"hostid": "10", "interfaces": [_AGENT_IF, _SNMP_IF]}],
            {"hostids": ["10"]},
        )
        with ctx:
            result = await zabbix_host_interface_update(interfaceid="6", port="1161")
        methods = [c.args[0] for c in mock.call.call_args_list]
        assert methods == ["hostinterface.get", "host.get", "host.update"]
        ifaces = mock.call.call_args_list[2].args[1]["interfaces"]
        by_id = {i["interfaceid"]: i for i in ifaces}
        assert by_id["6"]["port"] == "1161"
        assert by_id["5"]["port"] == "10050"   # other interface untouched
        assert result == {"interfaceids": ["6"]}

    async def test_no_change_does_not_write(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_seq([{"interfaceid": "5", "hostid": "10"}])
        with ctx:
            result = await zabbix_host_interface_update(interfaceid="5")
        methods = [c.args[0] for c in mock.call.call_args_list]
        assert methods == ["hostinterface.get"]
        assert result == {"interfaceids": ["5"]}

    async def test_unknown_interface_raises(self, zabbix_env: dict) -> None:
        from zabbix_mcp.errors import ZabbixNotFoundError
        mock, ctx = _mock_client_seq([])
        with ctx, pytest.raises(ZabbixNotFoundError):
            await zabbix_host_interface_update(interfaceid="99", port="1")
        assert mock.call.call_count == 1


from zabbix_mcp.tools.host import zabbix_host_delete, zabbix_host_interface_delete  # noqa: E402


class TestZabbixHostDelete:
    async def test_calls_host_delete(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({"hostids": ["10", "11"]})
        with ctx:
            result = await zabbix_host_delete(hostids=["10", "11"])
        assert mock.call.call_args[0][0] == "host.delete"
        assert result == {"hostids": ["10", "11"]}

    async def test_passes_ids_as_positional(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client({})
        with ctx:
            await zabbix_host_delete(hostids=["5"])
        assert mock.call.call_args[0][1] == ["5"]

    async def test_destructive_annotation(self, zabbix_env: dict) -> None:
        from zabbix_mcp.tools.host import DELETE
        assert DELETE["destructiveHint"] is True


class TestZabbixHostInterfaceDelete:
    async def test_uses_host_update_without_deleted_interface(self, zabbix_env: dict) -> None:
        mock, ctx = _mock_client_seq(
            [{"interfaceid": "6", "hostid": "10"}],
            [{"hostid": "10", "interfaces": [_AGENT_IF, _SNMP_IF]}],
            {"hostids": ["10"]},
        )
        with ctx:
            result = await zabbix_host_interface_delete(interfaceids=["6"])
        methods = [c.args[0] for c in mock.call.call_args_list]
        assert methods == ["hostinterface.get", "host.get", "host.update"]
        assert "hostinterface.delete" not in methods
        ifaces = mock.call.call_args_list[2].args[1]["interfaces"]
        assert [i["interfaceid"] for i in ifaces] == ["5"]
        assert result == {"interfaceids": ["6"]}

    async def test_multiple_hosts(self, zabbix_env: dict) -> None:
        other = {**_AGENT_IF, "interfaceid": "8", "hostid": "11"}
        other_keep = {**_AGENT_IF, "interfaceid": "9", "hostid": "11", "main": "0"}
        mock, ctx = _mock_client_seq(
            [{"interfaceid": "6", "hostid": "10"}, {"interfaceid": "9", "hostid": "11"}],
            [{"hostid": "10", "interfaces": [_AGENT_IF, _SNMP_IF]}],
            {"hostids": ["10"]},
            [{"hostid": "11", "interfaces": [other, other_keep]}],
            {"hostids": ["11"]},
        )
        with ctx:
            await zabbix_host_interface_delete(interfaceids=["6", "9"])
        updates = [c.args[1] for c in mock.call.call_args_list if c.args[0] == "host.update"]
        assert [(u["hostid"], [i["interfaceid"] for i in u["interfaces"]]) for u in updates] == [
            ("10", ["5"]),
            ("11", ["8"]),
        ]

    async def test_unknown_interface_raises_before_any_write(self, zabbix_env: dict) -> None:
        from zabbix_mcp.errors import ZabbixNotFoundError
        mock, ctx = _mock_client_seq([{"interfaceid": "6", "hostid": "10"}])
        with ctx, pytest.raises(ZabbixNotFoundError):
            await zabbix_host_interface_delete(interfaceids=["6", "404"])
        assert mock.call.call_count == 1

    async def test_api_error_propagates(self, zabbix_env: dict) -> None:
        """Interface still used by items: Zabbix refuses host.update, error must surface."""
        from zabbix_mcp.errors import ZabbixAPIError
        mock, ctx = _mock_client_seq(
            [{"interfaceid": "6", "hostid": "10"}],
            [{"hostid": "10", "interfaces": [_AGENT_IF, _SNMP_IF]}],
            ZabbixAPIError("Interface is linked to item"),
        )
        with ctx, pytest.raises(ZabbixAPIError):
            await zabbix_host_interface_delete(interfaceids=["6"])
