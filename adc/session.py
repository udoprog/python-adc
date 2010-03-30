class ADCSession:
  PROTOCOL, IDENTIFY, VERIFY, NORMAL, DATA = range(5);
  
  def __init__(self):
    # intial state should always be protocol
    self.state = PROTOCOL;
