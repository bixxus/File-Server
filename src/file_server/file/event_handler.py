from watchdog.events import FileSystemEventHandler

from file_server.packet.impl import FileChangePacket, FileAddPacket, FileDeletePacket, FileMovePacket

from time import sleep
from threading import Thread


class EventHandler(FileSystemEventHandler):

    events_to_ignore = {}

    def add_ignore(self, data):
        if data in EventHandler.events_to_ignore:
            EventHandler.events_to_ignore[data] += 1
        else:
            EventHandler.events_to_ignore[data] = 1

    def __init__(self, hub_processor, directory):
        self.hub_processor = hub_processor
        self.directory = directory

    def send_file_contents(self, file_name, packet_class, data, count=0):
        try:
            with open(self.directory + file_name, mode='rb') as file:
                pass

            self.hub_processor.queue_packet(
                packet_class(
                    self.hub_processor,
                    file_name=file_name
                ), data
            )
        except PermissionError:
            # Wait until we can actually read the file
            sleep(500)
            self.send_file_contents(file_name, packet_class, data, count + 1)

    def on_created(self, event):
        if (event.is_directory): 
            print("Created directory: " + str(event.src_path))
            return False

        file_name = event.src_path[len(self.directory):]

        data = ("change", file_name)

        print("Local File Modified: {}".format(file_name))

        if not data in EventHandler.events_to_ignore:
            Thread(target = self.send_file_contents, args = [file_name, FileAddPacket, data]).start()
        else:
            if EventHandler.events_to_ignore[data] == 1:
                del EventHandler.events_to_ignore[data]
            else:
                EventHandler.events_to_ignore[data] -= 1

    def on_modified(self, event):
        if (event.is_directory): 
            print("Modified directory: " + str(event.src_path))
            return False

        file_name = event.src_path[len(self.directory):]

        data = ("change", file_name)

        print("Local File Modified: {}".format(file_name))

        if not data in EventHandler.events_to_ignore:
            Thread(target = self.send_file_contents, args = [file_name, FileChangePacket, data]).start()
        else:
            if EventHandler.events_to_ignore[data] == 1:
                del EventHandler.events_to_ignore[data]
            else:
                EventHandler.events_to_ignore[data] -= 1

    def on_deleted(self, event):
        if (event.is_directory): 
            print("Deleted directory: " + str(event.src_path))
            return False

        file_name = event.src_path[len(self.directory):]

        print("Local File Deleted: {}".format(file_name))

        data = ("delete", file_name)

        if not data in EventHandler.events_to_ignore:
            self.hub_processor.queue_packet(
                FileDeletePacket(
                    self.hub_processor,
                    file_name=file_name
                ), data
            )
        else:
            if EventHandler.events_to_ignore[data] == 1:
                del EventHandler.events_to_ignore[data]
            else:
                EventHandler.events_to_ignore[data] -= 1

    def on_moved(self, event):
        if (event.is_directory): 
            print("Moved directory: " + str(event.src_path))
            return False

        file_name = event.src_path[len(self.directory):]
        new_name = event.dest_path[len(self.directory):]

        print("Local File Moved: {}".format(file_name))

        data = ("move", file_name, new_name)

        if not data in EventHandler.events_to_ignore:
            self.hub_processor.queue_packet(
                FileMovePacket(
                    self.hub_processor,
                    file_name=file_name,
                    new_name=new_name
                ), data
            )
        else:
            if EventHandler.events_to_ignore[data] == 1:
                del EventHandler.events_to_ignore[data]
            else:
                EventHandler.events_to_ignore[data] -= 1