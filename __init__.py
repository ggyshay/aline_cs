import logging
from ableton.v3.control_surface import ElementsBase
from ableton.v3.control_surface import (
    ControlSurface,
    ControlSurfaceSpecification,
)
from ableton.v3.control_surface.capabilities import (
    CONTROLLER_ID_KEY,
    NOTES_CC,
    PORTS_KEY,
    REMOTE,
    SCRIPT,
    controller_id,
    inport,
    outport,
)
from Live.Clip import MidiNoteSpecification  # type: ignore

logger = logging.getLogger("aline")


def get_capabilities():
    return {
        CONTROLLER_ID_KEY: controller_id(
            vendor_id=589180224,
            product_ids=[1161],
            model_name=["ARAv2"],
        ),
        PORTS_KEY: [inport(props=[NOTES_CC, SCRIPT, REMOTE]), outport(props=[SCRIPT])],
    }


class Elements(ElementsBase):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)


class Specification(ControlSurfaceSpecification):
    elements_type = Elements


def create_instance(c_instance):
    return Nopia(Specification, c_instance=c_instance)


class Nopia(ControlSurface):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)

        self.log_level = "info"

        self.show_message("Aline: Hello!")
        logger.info("Aline: init started ...")

        self.selected_track = None

    def setup(self):
        super().setup()

    # def handle_tempo(self, msb, lsb):
    #     tempo = (msb << 8 | lsb) / 256
    #     logger.info(f"tempo: {tempo}")
    #     self.song.tempo = tempo

    # def handle_scale(self, mode, scale):
    #     logger.info(f"scale: {mode}, {scale}")
    #     self.song.root_note = scale
    #     self.song.scale_mode = True
    #     self.song.scale_name = mode_to_name[mode]

    # def volume_bass(self, volume):
    #     logger.info(f"bass volume: {volume}")
    #     if self.bass_track is None:
    #         self.show_message("Bass track not found")
    #         return

    #     self.bass_track.mixer_device.volume.value = volume / 127

    # def volume_pad(self, volume):
    #     logger.info(f"pad volume: {volume}")
    #     if self.pad_track is None:
    #         self.show_message("Pad track not found")
    #         return

    #     self.pad_track.mixer_device.volume.value = volume / 127

    # def change_inputs(self):
    #     if (self.pad_track is None) or (self.bass_track is None):
    #         return
    #     types = self.pad_track.available_input_routing_types
    #     logger.info(f"types({len(types)}): {types}")
    #     for i in range(len(types)):
    #         logger.info(types[i].display_name)
    #         if "Nopia Input" in types[i].display_name:
    #             self.pad_track.input_routing_type = types[i]
    #             self.bass_track.input_routing_type = types[i]

    #     channels = self.pad_track.available_input_routing_channels
    #     logger.info(f"channels({len(channels)}): {channels}")
    #     for i in range(len(channels)):
    #         logger.info(channels[i].display_name)
    #         if "Ch. 1" == channels[i].display_name:
    #             self.bass_track.input_routing_channel = channels[i]
    #             self.pad_track.input_routing_channel = channels[i + 1]
    #             break

    #     self.pad_track.arm = True
    #     self.bass_track.arm = True

    # def create_channels(self):
    #     logger.info("creating channels")

    #     # Bass ======================
    #     self.bass_track = self.song.create_midi_track(-1)
    #     self.bass_track.name = "Bass (Nopia)"
    #     self.bass_track.color = 0x00C4EDA9
    #     for c in self.application.browser.user_library.iter_children:
    #         if c.name == "Nopia":
    #             for cc in c.iter_children:
    #                 if "bass" in cc.name:
    #                     self.application.browser.load_item(cc)
    #                     break
    #             break

    #     # Pad ======================
    #     self.pad_track = self.song.create_midi_track(-1)
    #     self.pad_track.name = "Pad (Nopia)"
    #     self.pad_track.color = 0x00C4EDA9
    #     for c in self.application.browser.user_library.iter_children:
    #         if c.name == "Nopia":
    #             for cc in c.iter_children:
    #                 if "pad" in cc.name:
    #                     self.application.browser.load_item(cc)
    #                     break
    #             break

    #     self.schedule_message(2, self.change_inputs)
    def ensure_selected_track(self):

        pass

    def create_clip(self, length=1):
        # self.clip = self.song.view.selected_track.clip_slots[0].create_clip(length)
        selected_track = self.song.view.selected_track
        i = 0
        while selected_track.clip_slots[i].has_clip:
            i += 1
        if i >= len(selected_track.clip_slots):
            self.show_message("No more clip slots available")
            return
        self.clip = selected_track.clip_slots[i].create_clip(length/4)
        selected_track.clip_slots[i].fire()



    def add_note(
        self,
        start,
        duration,
        pitch,
        vel,
    ):
        logger.info(f"add note: {start}, {duration}, {pitch}, {vel}")
        note = MidiNoteSpecification(
            pitch=pitch,
            start_time=start/4,
            duration=duration/4,
            velocity=vel,
            mute=False,
        )
        self.clip.add_new_notes((note,))
        self.clip.deselect_all_notes()

    def process_midi_bytes(self, data, midi_processor):
        logger.info(f"midi bytes: {data}")
        self.ensure_selected_track()
        if data[0] != 0xF0:
            return
        if data[1] != 0x13:
            self.create_clip(data[2])
            return
        # {
        #                              0xF0,
        #                              0x13,
        #                              (byte)(start & 0xFF),
        #                              (byte)((start >> 8) & 0xFF),
        #                              (byte)((start >> 16) & 0xFF),
        #                              (byte)((start >> 24) & 0xFF),
        #                              (byte)(duration & 0xFF),
        #                              (byte)((duration >> 8) & 0xFF),
        #                              (byte)((duration >> 16) & 0xFF),
        #                              (byte)((duration >> 24) & 0xFF),
        #                              pitch,
        #                              vel,
        #                              0xF7};
        start = data[2] | (data[3] << 7) | (data[4] << 14) | (data[5] << 21)
        duration = data[6] | (data[7] << 7) | (data[8] << 14) | (data[9] << 21)
        duration = duration/16.0
        pitch = data[10]
        vel = data[11]
        logger.info(f"start: {start}, duration: {duration}, pitch: {pitch}, vel: {vel}")
        self.add_note(
            start,
            duration,
            pitch,
            vel,
        )

    def disconnect(self):
        self.show_message("Disconnecting...")
        logger.info("Disconnecting...")
        self.stop_logging()
        super().disconnect()
