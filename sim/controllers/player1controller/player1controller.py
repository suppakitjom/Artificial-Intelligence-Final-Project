from controller import Robot, Receiver, Emitter
import json

class E_puckController(Robot):
    def __init__(self):
        super().__init__()
        self.receiver = self.getDevice("receiver1")
        self.emitter = self.getDevice("emitter1")
        self.receiver.enable(int(self.getBasicTimeStep()))
        self.emitter.setChannel(1)  # Set the channel to match configuration
        self.left_motor = self.getDevice("left wheel motor")
        self.right_motor = self.getDevice("right wheel motor")
        self.left_motor.setPosition(float('inf'))  # Set to infinity for velocity control
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)

    def run(self):
        while self.step(int(self.getBasicTimeStep())) != -1:
            if self.receiver.getQueueLength() > 0:
                message = self.receiver.getData().decode('utf-8')
                command = json.loads(message)
                if command['action'] == 'move':
                    self.move(command['distance'], command['speed'])
                    self.send_move_done_message()
                self.receiver.nextPacket()

    def move(self, distance, speed):
        # Simple move logic - move forward for 'distance' at 'speed'
        travel_time = distance / speed
        self.left_motor.setVelocity(speed)
        self.right_motor.setVelocity(speed)
        start_time = self.getTime()
        while self.getTime() - start_time < travel_time:
            if self.step(int(self.getBasicTimeStep())) == -1:
                break
        self.left_motor.setVelocity(0)
        self.right_motor.setVelocity(0)

    def send_move_done_message(self):
        # Send a message back to the supervisor or another controller
        message = json.dumps({"status": "move_done"}).encode('utf-8')
        self.emitter.send(message)

if __name__ == "__main__":
    controller = E_puckController()
    controller.run()
