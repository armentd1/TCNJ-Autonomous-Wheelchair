"""
File: serial_communication.py

Project: TCNJ Autonomous Wheelchair
Component: Stage 2 - Python Communication Client

Purpose:
    Provide a reusable Python interface for sending commands to the
    Arduino and reading its responses.

Supported commands:
    PING
    STATUS

Expected responses:
    PING   -> OK,PONG
    STATUS -> OK,STATUS,PROTOCOL_READY

Design:
    The client accepts a serial connection object.

    This allows us to use:
        1. A simulated connection for development.
        2. A real PySerial connection when hardware is available.

IMPORTANT:
    This module does not control motors or wheelchair movement.
"""

# Import PySerial's exception type for handling serial errors.
from copy import error

from serial import SerialException

# ---------------------------------------------------------------------
# 1. CUSTOM EXCEPTIONS
# ---------------------------------------------------------------------

class CommunicationError(Exception):
    """
    Base exception for communication-related problems.

    Using a dedicated exception type makes it easier for other
    software components to recognize communication failures.
    """
    pass


class CommunicationTimeout(CommunicationError):
    """
    Raised when the Arduino does not provide a complete response
    within the serial connection's configured timeout.
    """
    pass


class InvalidResponse(CommunicationError):
    """
    Raised when a response does not match the expected protocol.
    """
    pass


# ---------------------------------------------------------------------
# 2. COMMUNICATION CLIENT
# ---------------------------------------------------------------------

class ArduinoCommunication:
    """
    Manages command/response communication with an Arduino.

    Parameters:
        serial_connection:
            A PySerial-compatible connection object.

    The connection must provide:
        write(data)
        readline()
        close()
        is_open

    In this stage, we can provide a simulated connection with
    those same methods.
    """

    # These are the only commands supported by our Stage 1 firmware.
    SUPPORTED_COMMANDS = {
        "PING": "OK,PONG",
        "STATUS": "OK,STATUS,PROTOCOL_READY"
    }

    def __init__(self, serial_connection):
        """
        Store the serial connection.

        We deliberately do not open a hardware port here.

        This separates communication logic from the physical
        connection setup and makes simulated testing possible.
        """
        self.serial_connection = serial_connection

    def is_connected(self):
        """
        Report whether the serial connection is open.

        Note:
            An open serial port does not guarantee that the
            Arduino is connected, running, or responding.
        """
        return self.serial_connection.is_open

    def send_command(self, command):
        """
        Send one supported command and read its response.

        Parameters:
            command (str):
                The command to send, such as "PING".

        Returns:
            str:
                The decoded response from the Arduino.

        Raises:
            ValueError:
                If the command is unsupported.

            CommunicationError:
                If the connection is closed or a serial operation fails.

            CommunicationTimeout:
                If no complete response is received.

            InvalidResponse:
                If the response does not match the expected protocol.
        """

        # Validate the command before sending anything.
        #
        # This prevents the Python program from accidentally
        # transmitting unsupported commands.
        if command not in self.SUPPORTED_COMMANDS:
            raise ValueError(
                f"Unsupported command: {command}"
            )

        # Verify that the connection is open.
        if not self.is_connected():
            raise CommunicationError(
                "Serial connection is not open."
            )

        # The Arduino firmware expects newline-terminated commands.
        #
        # Example:
        #   "PING" becomes b"PING\n"
        #
        # The b prefix indicates binary data (bytes).
        message = (command + "\n").encode("ascii")

        try:
            # Send the command.
            self.serial_connection.write(message)

            # Read one response line.
            #
            # For a real PySerial connection, readline() uses the
            # timeout configured when opening the serial port.
            response_bytes = self.serial_connection.readline()

        except (OSError, SerialException) as error:
            raise CommunicationError(
                f"Serial communication failed: {error}"
            ) from error

        # If no bytes were received, the read timed out.
        if not response_bytes:
            raise CommunicationTimeout(
                f"No response received for {command}."
            )

        # A valid protocol response must end with a newline.
        #
        # If the Arduino sends only part of a line before the
        # timeout, we reject it rather than treating it as valid.
        if not response_bytes.endswith(b"\n"):
            raise CommunicationTimeout(
                f"Incomplete response received for {command}."
            )

        try:
            # Convert the received bytes into readable text.
            #
            # strip() removes the newline and any carriage return.
            response = response_bytes.decode("ascii").strip()

        except UnicodeDecodeError as error:
            raise InvalidResponse(
                "Response contains invalid ASCII characters."
            ) from error

        # The Stage 1 Arduino firmware has one expected successful
        # response for each supported command.
        expected_response = self.SUPPORTED_COMMANDS[command]

        if response != expected_response:
            raise InvalidResponse(
                f"Expected '{expected_response}', "
                f"but received '{response}'."
            )

        return response

    def ping(self):
        """
        Check whether the Arduino responds to a PING command.
        """
        return self.send_command("PING")

    def get_status(self):
        """
        Request the Arduino communication firmware's status.

        PROTOCOL_READY means the parser is responding.
        It does not indicate that wheelchair hardware is ready.
        """
        return self.send_command("STATUS")

    def close(self):
        """
        Close the serial connection if it is currently open.
        """
        if self.is_connected():
            self.serial_connection.close()