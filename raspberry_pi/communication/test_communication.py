"""
File: test_communication.py

Project: TCNJ Autonomous Wheelchair
Component: Stage 2 - Simulated Communication Tests

Purpose:
    Test the Python communication client without requiring
    a Raspberry Pi or physical Arduino.

This file simulates:
    - Successful PING responses
    - Successful STATUS responses
    - Communication timeouts
    - Unexpected responses
    - Closed serial connections

IMPORTANT:
    This simulator imitates selected protocol responses.
    It does not execute the actual Arduino firmware.
"""

from serial_communication import (
    ArduinoCommunication,
    CommunicationError,
    CommunicationTimeout,
    InvalidResponse
)


# ---------------------------------------------------------------------
# 1. SIMULATED SERIAL CONNECTION
# ---------------------------------------------------------------------

class FakeSerial:
    """
    A minimal simulated serial connection.

    This class provides the methods expected by
    ArduinoCommunication.

    It does not connect to any physical device.
    """

    def __init__(self):
        """
        Initialize the simulated connection.
        """

        # Simulate an initially open connection.
        self.is_open = True

        # Store the most recently transmitted command.
        self.last_written = None

        # Store the response that readline() will return.
        self.next_response = b""

    def write(self, data):
        """
        Simulate transmitting data to the Arduino.

        Parameters:
            data (bytes):
                The command transmitted by the Python client.
        """

        if not self.is_open:
            raise OSError("Simulated serial port is closed.")

        # Record the transmitted bytes for inspection.
        self.last_written = data

        # Simulate how our Stage 1 Arduino firmware responds.
        if data == b"PING\n":
            self.next_response = b"OK,PONG\r\n"

        elif data == b"STATUS\n":
            self.next_response = (
                b"OK,STATUS,PROTOCOL_READY\r\n"
            )

        else:
            self.next_response = b"ERR,UNKNOWN_COMMAND\r\n"

        # PySerial's write() normally returns the number
        # of bytes written.
        return len(data)

    def readline(self):
        """
        Return the simulated Arduino response.
        """

        if not self.is_open:
            raise OSError("Simulated serial port is closed.")

        return self.next_response

    def close(self):
        """
        Simulate closing the serial connection.
        """
        self.is_open = False


# ---------------------------------------------------------------------
# 2. TEST FUNCTIONS
# ---------------------------------------------------------------------

def test_ping():
    """
    Verify that PING produces the expected response.
    """

    fake_serial = FakeSerial()
    arduino = ArduinoCommunication(fake_serial)

    response = arduino.ping()

    assert response == "OK,PONG"
    assert fake_serial.last_written == b"PING\n"

    print("PASS: PING command")


def test_status():
    """
    Verify that STATUS produces the expected response.
    """

    fake_serial = FakeSerial()
    arduino = ArduinoCommunication(fake_serial)

    response = arduino.get_status()

    assert response == "OK,STATUS,PROTOCOL_READY"

    print("PASS: STATUS command")


def test_timeout():
    """
    Verify that a missing response produces a timeout.

    We override readline() to simulate a serial port
    that returns no data before its timeout.
    """

    fake_serial = FakeSerial()

    fake_serial.readline = lambda: b""

    arduino = ArduinoCommunication(fake_serial)

    try:
        arduino.ping()

    except CommunicationTimeout:
        print("PASS: Timeout detected")

    else:
        raise AssertionError(
            "Expected CommunicationTimeout was not raised."
        )


def test_invalid_response():
    """
    Verify that an unexpected response is rejected.
    """

    fake_serial = FakeSerial()

    fake_serial.readline = lambda: b"WRONG_RESPONSE\n"

    arduino = ArduinoCommunication(fake_serial)

    try:
        arduino.ping()

    except InvalidResponse:
        print("PASS: Invalid response detected")

    else:
        raise AssertionError(
            "Expected InvalidResponse was not raised."
        )


def test_closed_connection():
    """
    Verify that commands cannot be sent through
    a closed serial connection.
    """

    fake_serial = FakeSerial()
    arduino = ArduinoCommunication(fake_serial)

    arduino.close()

    try:
        arduino.ping()

    except CommunicationError:
        print("PASS: Closed connection detected")

    else:
        raise AssertionError(
            "Expected CommunicationError was not raised."
        )


def test_unsupported_command():
    """
    Verify that unsupported commands are rejected
    before they reach the simulated Arduino.
    """

    fake_serial = FakeSerial()
    arduino = ArduinoCommunication(fake_serial)

    try:
        arduino.send_command("MOVE")

    except ValueError:
        print("PASS: Unsupported command rejected")

    else:
        raise AssertionError(
            "Expected ValueError was not raised."
        )


# ---------------------------------------------------------------------
# 3. RUN ALL TESTS
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print("Starting simulated communication tests...\n")

    test_ping()
    test_status()
    test_timeout()
    test_invalid_response()
    test_closed_connection()
    test_unsupported_command()

    print("\nAll Stage 2 simulation tests passed.")