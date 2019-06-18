#  No Warranty or Liability.  The code contained herein is being supplied to Licensee
#  "AS IS" without any warranty of any kind.  OSIsoft DISCLAIMS ALL EXPRESS AND IMPLIED WARRANTIES,
#  INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#  PURPOSE and NONINFRINGEMENT. In no event will OSIsoft be liable to Licensee or to any third party
#  for damages of any kind arising from Licensee's use of the this code OR OTHERWISE, including
#  but not limited to direct, indirect, special, incidental and consequential damages, and Licensee
#  expressly assumes the risk of all such damages.  FURTHER, THIS CODE IS NOT ELIGIBLE FOR
#  SUPPORT UNDER EITHER OSISOFT'S STANDARD OR ENTERPRISE LEVEL SUPPORT AGREEMENTS

# Credit to Maxim for the work done here:
# https://github.com/uzumaxy/pymodbus3

# Import the various server implementations
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from threading import Thread
from time import sleep
from os import popen
from sys import exit

# Configure logging
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Define the function that updates the registers
CONTINUE_UPDATING_MODBUS_REGISTERS = False


def update_modbus_registers(args):
    log.debug("Updated thread started.")
    update_interval_seconds = 5
    heartbeat_counter = 1
    heartbeat_counter_max_value = 10
    register_type = 4
    register_offset = 0
    while (CONTINUE_UPDATING_MODBUS_REGISTERS is True):
        log.debug("Updating the server registers")
        simulated_modbus_server_context = args[0]
        # Read the board temperature
        temperature = 1
        try:
            temperature = int((float(popen("vcgencmd measure_temp").readline().replace("temp=", "").replace("'C", "")) * 9 / 5 + 32) * 100)
        except Exception as ex:
            # Log any error, if it occurs
            log.debug("Error reading temperature: " + str(ex))
        # Write the new values back to the Modbus register
        new_register_values = [temperature, heartbeat_counter]
        log.debug("New values: " + str(new_register_values))
        simulated_modbus_server_context.setValues(register_type, register_offset, new_register_values)
        # Increment the hearbeat counter by one
        heartbeat_counter = heartbeat_counter + 1
        # Reset the counter if necessary
        if (heartbeat_counter > heartbeat_counter_max_value):
            heartbeat_counter = 1
        # Wait until the next loop
        sleep(update_interval_seconds)
    # Once broken out of the loop, note that the thread is over
    log.debug("Updated thread ended.")

# Specify the Modbus server address and port
MODBUS_SERVER_ADDRESS = "localhost"
MODBUS_SERVER_PORT = 502

# Specify the register map defaults
starting_register_offset = 0
number_of_registers_to_populate = 4
default_register_value = 31416
create_only_a_single_modbus_slave = True

# Populate the registers for a single Modbus slave
simulated_modbus_slave_context = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(starting_register_offset, [default_register_value] * number_of_registers_to_populate),
    co=ModbusSequentialDataBlock(starting_register_offset, [default_register_value] * number_of_registers_to_populate),
    hr=ModbusSequentialDataBlock(starting_register_offset, [default_register_value] * number_of_registers_to_populate),
    ir=ModbusSequentialDataBlock(starting_register_offset, [default_register_value] * number_of_registers_to_populate))

# Populate the modbus server with this single modbus slave
simulated_modbus_server_context = ModbusServerContext(slaves=simulated_modbus_slave_context, single=create_only_a_single_modbus_slave)

# Initialize the server information
simulated_modbus_server_identity = ModbusDeviceIdentification()
simulated_modbus_server_identity.VendorName = 'pymodbus'
simulated_modbus_server_identity.ProductCode = 'PM'
simulated_modbus_server_identity.VendorUrl = 'http://github.com/bashwork/pymodbus/'
simulated_modbus_server_identity.ProductName = 'pymodbus Server'
simulated_modbus_server_identity.ModelName = 'pymodbus Server'
simulated_modbus_server_identity.MajorMinorRevision = '1.0'

try:
    # Initialize the thread that will start updating our Modbus server's registers
    CONTINUE_UPDATING_MODBUS_REGISTERS = True
    update_registers_thread = Thread(target=update_modbus_registers, args=(simulated_modbus_server_context,))
    update_registers_thread.daemon = True
    update_registers_thread.start()

    # Run the server
    log.debug("Starting Modbus server; press CTRL+C or CTRL+Z to exit...")
    StartTcpServer(
        simulated_modbus_server_context,
        identity=simulated_modbus_server_identity,
        address=(MODBUS_SERVER_ADDRESS, MODBUS_SERVER_PORT)
    )
except (KeyboardInterrupt, SystemExit):
    log.debug("Stopping Modbus server...")
    log.debug("Stopping update thread...")
    CONTINUE_UPDATING_MODBUS_REGISTERS = False

log.debug("Script terminated.")
