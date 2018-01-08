from __future__ import absolute_import
import sys
import click
import logging
from click_datetime import Datetime
from pprint import pformat as pf

import os
import sys
sys.path.append(os.path.expanduser("~/Desktop/lights/pyHS100"))

from pyHS100 import (SmartDevice,
                     SmartPlug,
                     SmartBulb,
                     Discover)  # noqa: E402

pass_dev = click.make_pass_decorator(SmartDevice)


@click.group(invoke_without_command=True)
@click.option(u'--ip', envvar=u"PYHS100_IP", required=False)
@click.option(u'--debug/--normal', default=False)
@click.option(u'--bulb', default=False, is_flag=True)
@click.option(u'--plug', default=False, is_flag=True)
@click.pass_context
def cli(ctx, ip, debug, bulb, plug):
    u"""A cli tool for controlling TP-Link smart home plugs."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if ctx.invoked_subcommand == u"discover":
        return

    if ip is None:
        click.echo(u"No IP given, trying discovery..")
        ctx.invoke(discover)
        return

    elif ip is not None:
        if not bulb and not plug:
            click.echo(u"No --bulb nor --plug given, discovering..")
            devs = ctx.invoke(discover, discover_only=True)
            for discovered_ip, discovered_dev in devs:
                if discovered_ip == ip:
                    dev = discovered_dev
                    break
        elif bulb:
            dev = SmartBulb(ip)
        elif plug:
            dev = SmartPlug(ip)
        else:
            click.echo(u"Unable to detect type, use --bulb or --plug!")
            return
        ctx.obj = dev

    if ctx.invoked_subcommand is None:
        ctx.invoke(state)


@cli.command()
@click.option(u'--timeout', default=3, required=False)
@click.option(u'--discover-only', default=False)
@click.pass_context
def discover(ctx, timeout, discover_only):
    u"""Discover devices in the network."""
    click.echo(u"Discovering devices for %s seconds" % timeout)
    found_devs = Discover.discover(timeout=timeout).items()
    if not discover_only:
        for ip, dev in found_devs:
            ctx.obj = dev
            ctx.invoke(state)
            print

    return found_devs


@cli.command()
@pass_dev
def sysinfo(dev):
    u"""Print out full system information."""
    click.echo(click.style(u"== System info ==", bold=True))
    click.echo(pf(dev.sys_info))


@cli.command()
@pass_dev
@click.pass_context
def state(ctx, dev):
    u"""Print out device state and versions."""
    click.echo(click.style(u"== %s - %s ==" % (dev.alias, dev.model),
                           bold=True))

    click.echo(click.style(u"Device state: %s" % u"ON" if dev.is_on else u"OFF",
                           fg=u"green" if dev.is_on else u"red"))
    click.echo(u"IP address: %s" % dev.ip_address)
    for k, v in dev.state_information.items():
        click.echo(u"%s: %s" % (k, v))
    click.echo(click.style(u"== Generic information ==", bold=True))
    click.echo(u"Time:         %s" % dev.time)
    click.echo(u"Hardware:     %s" % dev.hw_info[u"hw_ver"])
    click.echo(u"Software:     %s" % dev.hw_info[u"sw_ver"])
    click.echo(u"MAC (rssi):   %s (%s)" % (dev.mac, dev.rssi))
    click.echo(u"Location:     %s" % dev.location)

    ctx.invoke(emeter)


@cli.command()
@pass_dev
@click.option(u'--year', type=Datetime(format=u'%Y'),
              default=None, required=False)
@click.option(u'--month', type=Datetime(format=u'%Y-%m'),
              default=None, required=False)
@click.option(u'--erase', is_flag=True)
def emeter(dev, year, month, erase):
    u"""Query emeter for historical consumption."""
    click.echo(click.style(u"== Emeter ==", bold=True))
    if not dev.has_emeter:
        click.echo(u"Device has no emeter")
        return

    if erase:
        click.echo(u"Erasing emeter statistics..")
        dev.erase_emeter_stats()
        return

    click.echo(u"Current state: %s" % dev.get_emeter_realtime())
    if year:
        click.echo(u"== For year %s ==" % year.year)
        click.echo(dev.get_emeter_monthly(year.year))
    elif month:
        click.echo(u"== For month %s of %s ==" % (month.month, month.year))
        dev.get_emeter_daily(year=month.year, month=month.month)


@cli.command()
@click.argument(u"brightness", type=click.IntRange(0, 100), default=None,
                required=False)
@pass_dev
def brightness(dev, brightness):
    u"""Get or set brightness. (Bulb Only)"""
    if brightness is None:
        click.echo(u"Brightness: %s" % dev.brightness)
    else:
        click.echo(u"Setting brightness to %s" % brightness)
        dev.brightness = brightness


@cli.command()
@click.argument(u"temperature", type=click.IntRange(2700, 6500), default=None,
                required=False)
@pass_dev
def temperature(dev, temperature):
    u"""Get or set color temperature. (Bulb only)"""
    if temperature is None:
        click.echo(u"Color temperature: %s" % dev.color_temp)
    else:
        click.echo(u"Setting color temperature to %s" % temperature)
        dev.color_temp = temperature


@cli.command()
@click.argument(u"h", type=click.IntRange(0, 360), default=None)
@click.argument(u"s", type=click.IntRange(0, 100), default=None)
@click.argument(u"v", type=click.IntRange(0, 100), default=None)
@pass_dev
def hsv(dev, h, s, v):
    u"""Get or set color in HSV. (Bulb only)"""
    if h is None or s is None or v is None:
        click.echo(u"Current HSV: %s" % dev.hsv)
    else:
        click.echo(u"Setting HSV: %s %s %s" % (h, s, v))
        dev.hsv = (h, s, v)


@cli.command()
@click.argument(u'state', type=bool, required=False)
@pass_dev
def led(dev, state):
    u"""Get or set led state. (Plug only)"""
    if state is not None:
        click.echo(u"Turning led to %s" % state)
        dev.led = state
    else:
        click.echo(u"LED state: %s" % dev.led)


@cli.command()
@pass_dev
def time(dev):
    u"""Get the device time."""
    click.echo(dev.time)


@cli.command()
@pass_dev
def on(plug):
    u"""Turn the device on."""
    click.echo(u"Turning on..")
    plug.turn_on()


@cli.command()
@pass_dev
def off(plug):
    u"""Turn the device off."""
    click.echo(u"Turning off..")
    plug.turn_off()


if __name__ == u"__main__":
    cli()
