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
# STAGE 3A - INCOMPLETE RESPONSE TESTS
# ---------------------------------------------------------------------

def test_incomplete_response():
    """
    Verify that the client rejects a response that never
    receives its terminating newline.

    A real serial connection could return partial data when
    the configured read timeout expires.
    """

    # Create a simulated serial connection.
    fake_serial = FakeSerial()

    # Replace the normal readline() behavior with a response
    # that is missing its newline terminator.
    fake_serial.readline = lambda: b"OK,PON"

    # Create the communication client.
    arduino = ArduinoCommunication(fake_serial)

    try:
        # Attempt to send PING and read the response.
        arduino.ping()

    except CommunicationTimeout:
        # The client correctly rejected the incomplete message.
        print("PASS: Incomplete response detected")

    else:
        # If no exception occurred, the test failed.
        raise AssertionError(
            "Expected CommunicationTimeout for incomplete response."
        )


def test_delayed_response_timeout():
    """
    Simulate a response that does not arrive before
    the serial read timeout.

    This test models the result of a timeout, rather than
    waiting for real elapsed time.
    """

    fake_serial = FakeSerial()

    # Simulate a serial read that timed out without receiving
    # any data.
    fake_serial.readline = lambda: b""

    arduino = ArduinoCommunication(fake_serial)

    try:
        arduino.get_status()

    except CommunicationTimeout:
        print("PASS: Delayed response timeout detected")

    else:
        raise AssertionError(
            "Expected CommunicationTimeout for delayed response."
        )


def test_invalid_ascii_response():
    """
    Verify that the client rejects a response containing
    bytes that cannot be decoded as ASCII.

    This simulates corrupted or unexpected serial data.
    """

    # Create a simulated serial connection.
    fake_serial = FakeSerial()

    # Replace readline() with a response containing
    # a byte that is invalid in ASCII.
    #
    # ASCII supports byte values from 0 through 127.
    # The byte \xff has a value of 255.
    fake_serial.readline = lambda: b"OK,\xff\n"

    # Create the communication client.
    arduino = ArduinoCommunication(fake_serial)

    try:
        # Attempt to send PING and decode the response.
        arduino.ping()

    except InvalidResponse:
        # The client correctly rejected the invalid data.
        print("PASS: Invalid ASCII response detected")

    else:
        # The test fails if no exception was raised.
        raise AssertionError(
            "Expected InvalidResponse for invalid ASCII data."
        )


def test_incorrect_command_response():
    """
    Verify that the client rejects a valid response
    that does not correspond to the command sent.

    This simulates receiving a response associated
    with a different command.
    """

    # Create a simulated serial connection.
    fake_serial = FakeSerial()

    # Replace readline() with a valid STATUS response.
    #
    # The client will send PING, so receiving a STATUS
    # response should be considered invalid.
    fake_serial.readline = lambda: (
        b"OK,STATUS,PROTOCOL_READY\r\n"
    )

    # Create the communication client.
    arduino = ArduinoCommunication(fake_serial)

    try:
        # Send PING and attempt to validate its response.
        arduino.ping()

    except InvalidResponse:
        # The client correctly rejected the mismatched response.
        print("PASS: Incorrect command response detected")

    else:
        # The test fails if the response was accepted.
        raise AssertionError(
            "Expected InvalidResponse for incorrect command response."
        )
    
def test_serial_read_failure():
    """
    Verify that the client handles an operating-system-level
    error occurring while reading a serial response.

    The simulated serial connection raises OSError
    instead of returning response bytes.
    """

    # Create a simulated serial connection.
    fake_serial = FakeSerial()

    # Define a function that simulates a failed read.
    def failed_read():
        raise OSError("Simulated serial read failure.")

    # Replace the normal readline() method with our
    # simulated failure function.
    fake_serial.readline = failed_read

    # Create the communication client.
    arduino = ArduinoCommunication(fake_serial)

    try:
        # Send PING and attempt to read its response.
        arduino.ping()

    except CommunicationError as error:
        # Verify that the error was converted into
        # our custom CommunicationError exception.
        assert type(error) is CommunicationError

        # Verify that the original error was preserved.
        assert isinstance(error.__cause__, OSError)

        print("PASS: Serial read failure detected")

    else:
        # The test fails if the client accepts the
        # failed read operation.
        raise AssertionError(
            "Expected CommunicationError for serial read failure."
        )

def test_serial_write_failure():
    """
    Verify that the client handles an operating-system-level
    error when attempting to write to the serial connection.

    The simulated connection raises OSError instead
    of successfully transmitting the command.
    """

    # Create a simulated serial connection.
    fake_serial = FakeSerial()

    # Simulate an operating-system-level write failure.
    def failed_write(message):
        raise OSError("Simulated serial write failure.")

    # Replace the normal write method.
    fake_serial.write = failed_write

    # Create the communication client.
    arduino = ArduinoCommunication(fake_serial)

    try:
        # Attempt to send a command.
        arduino.ping()

    except CommunicationError as error:
        # Verify that the correct custom exception was raised.
        assert type(error) is CommunicationError

        # Verify that the original error was preserved.
        assert isinstance(error.__cause__, OSError)

        print("PASS: Serial write failure detected")

    else:
        raise AssertionError(
            "Expected CommunicationError for serial write failure."
        )

def test_recovery_after_failure():
    """
    Verify that the communication client can successfully
    send another command after a previous command times out.

    The first read simulates a timeout.
    The second read returns a valid PING response.
    """

    fake_serial = FakeSerial()

    # Keep track of how many times readline() is called.
    read_count = 0

    def simulated_read():
        nonlocal read_count
        read_count += 1

        if read_count == 1:
            # First request: no response received.
            return b""

        # Second request: valid response received.
        return b"OK,PONG\n"

    # Replace the normal serial read behavior.
    fake_serial.readline = simulated_read

    arduino = ArduinoCommunication(fake_serial)

    # First attempt should time out.
    try:
        arduino.ping()

    except CommunicationTimeout:
        print("PASS: Initial communication timeout detected")

    else:
        raise AssertionError(
            "Expected CommunicationTimeout on first attempt."
        )

    # Second attempt should succeed using the same client.
    response = arduino.ping()

    assert response == "OK,PONG", (
        f"Expected 'OK,PONG', received '{response}'."
    )

    print("PASS: Communication recovered after failure")


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

    # Stage 3A Tests
    test_incomplete_response()
    test_delayed_response_timeout()
    test_invalid_ascii_response()
    test_incorrect_command_response()
    test_serial_read_failure()
    test_serial_write_failure()
    test_recovery_after_failure()

    print("\nAll communication tests passed.")