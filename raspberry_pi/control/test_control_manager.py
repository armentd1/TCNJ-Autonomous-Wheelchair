
"""
File: test_control_manager.py

Project: TCNJ Autonomous Wheelchair
Component: Stage 4 - Control Manager Testing

Purpose:
    Verify that the wheelchair control manager
    correctly initializes and handles basic
    operating-state transitions.
"""

from control_manager import (
    ControlManager,
    ControlState,
    MovementCommand,
    CommandSource
)


def test_initial_state():
    """
    Verify that the control manager starts in IDLE.
    """
    manager = ControlManager()

    assert manager.get_state() == ControlState.IDLE

    print("PASS: Control manager initializes in IDLE")


def test_manual_mode():
    """
    Verify that manual mode can be selected from IDLE.
    """
    manager = ControlManager()

    assert manager.request_manual_mode() is True
    assert manager.get_state() == ControlState.MANUAL

    print("PASS: Manual mode selected")


def test_autonomous_mode():
    """
    Verify that autonomous mode can be selected from IDLE.
    """
    manager = ControlManager()

    assert manager.request_autonomous_mode() is True
    assert manager.get_state() == ControlState.AUTONOMOUS

    print("PASS: Autonomous mode selected")


def test_direct_mode_switch_rejected():
    """
    Verify that the system cannot switch directly
    from MANUAL to AUTONOMOUS.
    """
    manager = ControlManager()

    manager.request_manual_mode()

    assert manager.request_autonomous_mode() is False
    assert manager.get_state() == ControlState.MANUAL

    print("PASS: Direct mode switch rejected")


def test_stop_request():
    """
    Verify that a stop request enters STOPPED.
    """
    manager = ControlManager()

    manager.request_manual_mode()
    manager.request_stop()

    assert manager.get_state() == ControlState.STOPPED

    print("PASS: Stop request changes state to STOPPED")


def test_fault_priority():
    """
    Verify that FAULT takes priority over other states.
    """
    manager = ControlManager()

    manager.request_autonomous_mode()
    manager.report_fault()

    assert manager.get_state() == ControlState.FAULT

    # A normal stop request must not clear FAULT.
    assert manager.request_stop() is False
    assert manager.get_state() == ControlState.FAULT

    print("PASS: Fault state retains priority")


def test_stop_reset_requires_confirmation():
    """
    Verify that STOPPED cannot be reset without
    explicit confirmation.
    """
    manager = ControlManager()

    manager.request_manual_mode()
    manager.request_stop()

    assert manager.reset_stop() is False
    assert manager.get_state() == ControlState.STOPPED

    print("PASS: Stop reset requires confirmation")


def test_successful_stop_reset():
    """
    Verify that an explicitly confirmed stop reset
    returns the manager to IDLE.
    """
    manager = ControlManager()

    manager.request_manual_mode()
    manager.request_stop()

    assert manager.reset_stop(ready_for_reset=True) is True
    assert manager.get_state() == ControlState.IDLE

    print("PASS: Stop reset returns to IDLE")


def test_fault_reset_requires_confirmation():
    """
    Verify that FAULT cannot be reset without
    explicit confirmation.
    """
    manager = ControlManager()

    manager.report_fault()

    assert manager.reset_fault() is False
    assert manager.get_state() == ControlState.FAULT

    print("PASS: Fault reset requires confirmation")


def test_successful_fault_reset():
    """
    Verify that an explicitly confirmed fault reset
    returns the manager to IDLE.
    """
    manager = ControlManager()

    manager.request_autonomous_mode()
    manager.report_fault()

    assert manager.reset_fault(fault_cleared=True) is True
    assert manager.get_state() == ControlState.IDLE

    print("PASS: Fault reset returns to IDLE")


def test_reset_does_not_resume_movement_mode():
    """
    Verify that resetting a stopped system does not
    automatically restore its previous operating mode.
    """
    manager = ControlManager()

    manager.request_autonomous_mode()
    manager.request_stop()

    assert manager.reset_stop(ready_for_reset=True) is True

    # The previous AUTONOMOUS mode must not be restored.
    assert manager.get_state() == ControlState.IDLE

    print("PASS: Reset does not resume previous mode")


def test_movement_command_creation():
    """
    Verify that a valid movement request can be created.
    """
    command = MovementCommand(
        linear_x=0.2,
        angular_z=0.0
    )

    assert command.linear_x == 0.2
    assert command.angular_z == 0.0

    print("PASS: Movement command created")


def test_zero_movement_command():
    """
    Verify that a zero-velocity request is valid.
    """
    command = MovementCommand(
        linear_x=0.0,
        angular_z=0.0
    )

    assert command.linear_x == 0.0
    assert command.angular_z == 0.0

    print("PASS: Zero movement command accepted")


def test_invalid_movement_command():
    """
    Verify that invalid numeric values are rejected.
    """

    invalid_values = [
        float("nan"),
        float("inf"),
        float("-inf"),
        "fast",
        None,
        True
    ]

    for value in invalid_values:
        try:
            MovementCommand(
                linear_x=value,
                angular_z=0.0
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                f"Invalid linear velocity was accepted: {value}"
            )

        try:
            MovementCommand(
                linear_x=0.0,
                angular_z=value
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                f"Invalid angular velocity was accepted: {value}"
            )

    print("PASS: Invalid movement commands rejected")


# ---------------------------------------------------------------------
# STAGE 4D - MOVEMENT AUTHORIZATION TESTS
# ---------------------------------------------------------------------

def test_manual_command_authorized():
    """
    Verify that a manual movement request is accepted
    when MANUAL mode is selected.
    """
    manager = ControlManager()
    manager.request_manual_mode()

    command = MovementCommand(0.2, 0.0)

    result = manager.authorize_movement(
        command,
        CommandSource.MANUAL
    )

    assert result is command

    print("PASS: Manual movement request authorized")


def test_autonomous_command_authorized():
    """
    Verify that an autonomous movement request is
    accepted when AUTONOMOUS mode is selected.
    """
    manager = ControlManager()
    manager.request_autonomous_mode()

    command = MovementCommand(0.2, 0.0)

    result = manager.authorize_movement(
        command,
        CommandSource.AUTONOMOUS
    )

    assert result is command

    print("PASS: Autonomous movement request authorized")


def test_manual_command_rejected_in_autonomous_mode():
    """
    Verify that manual commands are rejected when
    AUTONOMOUS mode is selected.
    """
    manager = ControlManager()
    manager.request_autonomous_mode()

    command = MovementCommand(0.2, 0.0)

    result = manager.authorize_movement(
        command,
        CommandSource.MANUAL
    )

    assert result is None

    print("PASS: Manual command rejected in autonomous mode")


def test_autonomous_command_rejected_in_manual_mode():
    """
    Verify that autonomous commands are rejected
    when MANUAL mode is selected.
    """
    manager = ControlManager()
    manager.request_manual_mode()

    command = MovementCommand(0.2, 0.0)

    result = manager.authorize_movement(
        command,
        CommandSource.AUTONOMOUS
    )

    assert result is None

    print("PASS: Autonomous command rejected in manual mode")


def test_movement_rejected_in_idle():
    """
    Verify that IDLE rejects movement requests.
    """
    manager = ControlManager()

    command = MovementCommand(0.2, 0.0)

    assert manager.authorize_movement(
        command,
        CommandSource.MANUAL
    ) is None

    assert manager.authorize_movement(
        command,
        CommandSource.AUTONOMOUS
    ) is None

    print("PASS: Movement rejected in IDLE")


def test_movement_rejected_when_stopped():
    """
    Verify that STOPPED rejects movement requests.
    """
    manager = ControlManager()
    manager.request_manual_mode()
    manager.request_stop()

    command = MovementCommand(0.2, 0.0)

    assert manager.authorize_movement(
        command,
        CommandSource.MANUAL
    ) is None

    assert manager.authorize_movement(
        command,
        CommandSource.AUTONOMOUS
    ) is None

    print("PASS: Movement rejected while STOPPED")


def test_movement_rejected_during_fault():
    """
    Verify that FAULT rejects movement requests.
    """
    manager = ControlManager()
    manager.request_autonomous_mode()
    manager.report_fault()

    command = MovementCommand(0.2, 0.0)

    assert manager.authorize_movement(
        command,
        CommandSource.MANUAL
    ) is None

    assert manager.authorize_movement(
        command,
        CommandSource.AUTONOMOUS
    ) is None

    print("PASS: Movement rejected during FAULT")


def test_invalid_authorization_inputs():
    """
    Verify that invalid command objects and
    unrecognized command sources are rejected.
    """
    manager = ControlManager()
    manager.request_manual_mode()

    command = MovementCommand(0.2, 0.0)

    assert manager.authorize_movement(
        "move forward",
        CommandSource.MANUAL
    ) is None

    assert manager.authorize_movement(
        command,
        "MANUAL"
    ) is None

    print("PASS: Invalid authorization inputs rejected")




if __name__ == "__main__":
    print("Starting control manager tests...\n")

    test_initial_state()
    test_manual_mode()
    test_autonomous_mode()
    test_direct_mode_switch_rejected()
    test_stop_request()
    test_fault_priority()
    test_stop_reset_requires_confirmation()
    test_successful_stop_reset()
    test_fault_reset_requires_confirmation()
    test_successful_fault_reset()
    test_reset_does_not_resume_movement_mode()
    test_movement_command_creation()
    test_zero_movement_command()
    test_invalid_movement_command()
        # Stage 4D Tests
    test_manual_command_authorized()
    test_autonomous_command_authorized()
    test_manual_command_rejected_in_autonomous_mode()
    test_autonomous_command_rejected_in_manual_mode()
    test_movement_rejected_in_idle()
    test_movement_rejected_when_stopped()
    test_movement_rejected_during_fault()
    test_invalid_authorization_inputs()

    print("\nAll control manager tests passed.")
