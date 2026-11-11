
"""
File: control_manager.py

Project: TCNJ Autonomous Wheelchair
Component: Stage 4 - Wheelchair Control Manager

Purpose:
    Manage the wheelchair's operating states and determine
    which control mode is currently selected.

    This initial version implements state management only.
    It does not send commands to motors, the Arduino,
    or any physical wheelchair hardware.
"""

from enum import Enum

from dataclasses import dataclass
import math

# ---------------------------------------------------------------------
# 1. OPERATING STATES
# ---------------------------------------------------------------------

class ControlState(Enum):
    """
    Defines the possible operating states of the wheelchair.

    IDLE:
        The system is initialized but not actively controlling
        movement.

    MANUAL:
        Manual control is selected.

    AUTONOMOUS:
        Autonomous navigation is selected.

    STOPPED:
        Movement is inhibited following a stop request.

    FAULT:
        A detected problem prevents normal operation.
    """

    IDLE = "IDLE"
    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"
    STOPPED = "STOPPED"
    FAULT = "FAULT"


# ---------------------------------------------------------------------
# COMMAND SOURCES
# ---------------------------------------------------------------------

class CommandSource(Enum):
    """
    Identifies the source of a movement request.

    MANUAL:
        Request from a manual-control interface.

    AUTONOMOUS:
        Request from autonomous navigation software.
    """

    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"


# ---------------------------------------------------------------------
# 2. MOVEMENT COMMAND
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class MovementCommand:
    """
    Represents a requested wheelchair movement.

    Parameters:
        linear_x:
            Requested forward/backward velocity in m/s.

        angular_z:
            Requested turning velocity in rad/s.

    IMPORTANT:
        This class only stores and validates a request.
        It does not operate motors or send serial commands.
    """

    linear_x: float
    angular_z: float

    def __post_init__(self):
        """
        Validate the values when a command is created.

        NaN and infinity are not meaningful velocity
        requests and must be rejected.
        """

        for name, value in (
            ("linear_x", self.linear_x),
            ("angular_z", self.angular_z)
        ):
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError(
                    f"{name} must be a numeric value."
                )

            if not math.isfinite(value):
                raise ValueError(
                    f"{name} must be a finite number."
                )


# ---------------------------------------------------------------------
# 2. CONTROL MANAGER
# ---------------------------------------------------------------------

class ControlManager:
    """
    Manages the wheelchair's software operating state.

    This class does not operate physical hardware.
    """

    def __init__(self):
        """
        Initialize the control manager.

        The wheelchair begins in IDLE, meaning no
        movement mode has been selected.
        """
        self.state = ControlState.IDLE

    def get_state(self):
        """
        Return the current operating state.
        """
        return self.state

    
    def request_manual_mode(self):
        """
        Request manual control.

        For this initial version, manual mode may only
        be selected while the system is IDLE.

        Returns:
            bool: True if the transition succeeds.
        """
        if self.state != ControlState.IDLE:
            return False

        self.state = ControlState.MANUAL
        return True

    def request_autonomous_mode(self):
        """
        Request autonomous control.

        Autonomous mode may only be selected
        while the system is IDLE.

        Returns:
            bool: True if the transition succeeds.
        """
        if self.state != ControlState.IDLE:
            return False

        self.state = ControlState.AUTONOMOUS
        return True

    def request_idle(self):
        """
        Return to IDLE from an active control mode.

        This initial version only changes the software
        state. It does not command physical hardware
        to stop.

        STOPPED and FAULT cannot be cleared using
        this method.
        """
        if self.state not in (
            ControlState.MANUAL,
            ControlState.AUTONOMOUS
        ):
            return False

        self.state = ControlState.IDLE
        return True

    def request_stop(self):
        """
        Inhibit movement by entering STOPPED.

        This is a software-state change only.
        It is not a physical emergency stop.
        """
        if self.state == ControlState.FAULT:
            return False

        self.state = ControlState.STOPPED
        return True

    def report_fault(self):
        """
        Enter FAULT after a problem is detected.

        Fault takes priority over other software states.
        """
        self.state = ControlState.FAULT
        return True

    
    def reset_stop(self, ready_for_reset=False):
        """
        Request recovery from the STOPPED state.

        Parameters:
            ready_for_reset (bool):
                Simulated confirmation that the conditions
                required for resetting have been satisfied.

        Returns:
            bool:
                True if the reset succeeds.
                False otherwise.

        IMPORTANT:
            This is a software-only demonstration.
            The readiness value is not verified against
            physical hardware.
        """

        # Only STOPPED can be cleared by this method.
        if self.state != ControlState.STOPPED:
            return False

        # Do not reset unless readiness is explicitly confirmed.
        if ready_for_reset is not True:
            return False

        # Return to IDLE, not the previous movement mode.
        self.state = ControlState.IDLE
        return True

    def reset_fault(self, fault_cleared=False):
        """
        Request recovery from the FAULT state.

        Parameters:
            fault_cleared (bool):
                Simulated confirmation that the underlying
                fault has been resolved.

        Returns:
            bool:
                True if the reset succeeds.
                False otherwise.

        IMPORTANT:
            This method does not diagnose or clear
            physical hardware faults.
        """

        # Only FAULT can be cleared by this method.
        if self.state != ControlState.FAULT:
            return False

        # Require explicit confirmation.
        if fault_cleared is not True:
            return False

        # Never automatically resume the previous mode.
        self.state = ControlState.IDLE
        return True

    
    # -----------------------------------------------------------------
    # MOVEMENT REQUEST AUTHORIZATION
    # -----------------------------------------------------------------

    def authorize_movement(self, command, source):
        """
        Determine whether a movement request is permitted
        by the currently selected software operating mode.

        Parameters:
            command (MovementCommand):
                The requested linear and angular velocity.

            source (CommandSource):
                The source requesting movement.

        Returns:
            MovementCommand:
                The original request if the source is permitted.

            None:
                If the request is rejected.

        IMPORTANT:
            This method does not operate motors, publish ROS
            messages, or transmit serial commands.

            It only performs basic software-mode authorization.
        """

        # Reject malformed command objects.
        if not isinstance(command, MovementCommand):
            return None

        # Reject unknown command sources.
        if not isinstance(source, CommandSource):
            return None

        # Never authorize movement while stopped or faulted.
        if self.state in (
            ControlState.STOPPED,
            ControlState.FAULT
        ):
            return None

        # Manual requests are permitted only in MANUAL mode.
        if self.state == ControlState.MANUAL:
            if source == CommandSource.MANUAL:
                return command

            return None

        # Autonomous requests are permitted only
        # in AUTONOMOUS mode.
        if self.state == ControlState.AUTONOMOUS:
            if source == CommandSource.AUTONOMOUS:
                return command

            return None

        # IDLE and any unexpected state reject movement.
        return None


