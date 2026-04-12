"""Core simulation tick loop."""

import logging

from .algorithms.base import BaseAlgorithm
from .config import SimConfig
from .io.reader import Request
from .io.writer import LogWriter
from .models.elevator import Direction, Elevator, ElevatorState
from .models.passenger import Passenger

logger = logging.getLogger(__name__)


class Simulation:
    def __init__(self, config: SimConfig, algorithm: BaseAlgorithm) -> None:
        self.config = config
        self.algorithm = algorithm
        self.elevators: list[Elevator] = [
            Elevator(id=i + 1, capacity=config.elevator_capacity)
            for i in range(config.num_elevators)
        ]
        self.passengers: list[Passenger] = []
        self.total_ticks: int = 0

    def run(self, requests: list[Request], writer: LogWriter) -> list[Passenger]:
        """Run the simulation to completion. Returns all passengers."""
        
        # just in case the rows in the file are not in ascending order by timestamp
        pending = sorted(requests, key=lambda r: r.time)
        logger.debug("Start simulation run for %s requests", len(pending))

        next_request_idx = 0
        tick = 0

        while True:
            logger.debug("Start tick #%s", tick)

            # 1. Release requests arriving at this tick (no peeking ahead).
            while next_request_idx < len(pending) and pending[next_request_idx].time == tick:
                req = pending[next_request_idx]

                self._sanity_check_req(req)

                passenger = Passenger(
                    id=req.id,
                    origin=req.source,
                    destination=req.dest,
                    request_time=req.time,
                )
                elevator = self.algorithm.pick_elevator_for_passenger(passenger, self.elevators)
                self.passengers.append(passenger)
                elevator.assign(passenger)
                logger.debug("assigned elevator %s to passenger %s", elevator.id, passenger.id)
                next_request_idx += 1

            # 2. Log positions at start of tick (before movement)
            writer.log_tick(tick, self.elevators)

            # 3. Process each elevator
            for elevator in self.elevators:
                # Count this tick as active if the elevator is not idle
                if elevator.state != ElevatorState.IDLE or elevator.destinations:
                    elevator.active_ticks += 1

                # Decrement stop countdown
                if elevator.stop_ticks_remaining > 0:
                    elevator.stop_ticks_remaining -= 1
                    continue  # still stopped — skip move

                # passengers exit at current floor
                arrived = elevator.exit(tick)

                # Board assigned passengers at current floor
                boarded = elevator.board(tick)

                for p in arrived:
                    writer.log_passenger(p)

                # If we boarded or exited anyone, apply stop penalty
                if (arrived or boarded) and self.config.stop_ticks > 0:
                    elevator.stop_ticks_remaining = self.config.stop_ticks
                    elevator.state = ElevatorState.STOPPED
                    continue

                # Set direction and move
                self._set_direction(elevator)
                logger.debug("Elevator %s will go %s", elevator.direction)

                elevator.move()

            # 4. End condition: all requests consumed and all passengers arrived
            all_requests_issued = next_request_idx >= len(pending)
            all_arrived = all(p.arrived for p in self.passengers)
            if not all_requests_issued:
                logger.debug("Continue loop because there are still more requests")
            elif not all_arrived:
                logger.debug("Continue loop because not all passengers have reached their destinations")
            else:
                break
            tick += 1

        self.total_ticks = tick + 1
        return self.passengers

    def _sanity_check_req(self, req: Request) -> None:
        if req.source > self.config.num_floors or req.dest > self.config.num_floors:
            logger.error(
                "The source %s and dest %s floor cannot exceed the number of floors %s",
                req.source, req.dest, self.config.num_floors,
            )
            exit(-1)
        elif req.source < 1 or req.dest < 1:
            logger.error(
                "The source %s and dest %s floor cannot be less than 1",
                req.source, req.dest,
            )
            exit(-1)

    def _set_direction(self, elevator: Elevator) -> None:
        num_floors = self.config.num_floors

        if not elevator.destinations:
            elevator.direction = Direction.IDLE
            elevator.state = ElevatorState.IDLE
            self._check_still_has_passengers(elevator)
            return

        above = [d for d in elevator.destinations if d > elevator.current_floor]
        below = [d for d in elevator.destinations if d < elevator.current_floor]

        # Continue in current direction if there are destinations that way
        if elevator.direction == Direction.UP and above:
            return
        if elevator.direction == Direction.DOWN and below:
            return

        # Reverse or pick a new direction
        if above:
            elevator.direction = Direction.UP
        elif below:
            elevator.direction = Direction.DOWN
        else:
            elevator.direction = Direction.IDLE
            elevator.state = ElevatorState.IDLE
            self._check_still_has_passengers(elevator)
            return

        # Sanity check: Floor boundary guard
        if elevator.current_floor <= 1 and elevator.direction == Direction.DOWN:
            elevator.direction = Direction.IDLE
            self._check_still_has_passengers(elevator)
        if elevator.current_floor >= num_floors and elevator.direction == Direction.UP:
            elevator.direction = Direction.IDLE
            self._check_still_has_passengers(elevator)

    def _check_still_has_passengers(self, elevator: Elevator) -> None:
        if len(elevator.passengers) > 0:
            logger.error("elevator %s still has %s passengers", elevator.id, len(elevator.passengers))
            exit(-1)