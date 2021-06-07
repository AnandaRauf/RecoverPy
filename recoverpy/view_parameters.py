import re
import py_cui

from recoverpy import views_handler as VIEWS_HANDLER
from recoverpy import helper as HELPER
from recoverpy import logger as LOGGER


class ParametersView:
    """Parameters menu is the first window displayed.
    User is prompted to select a partition and a string to search in it.

    Attributes:
        partition_to_search (str): Partition selected by user.
        string_to_search (str): String entered by user.
        partitions_dict (dict): Dictionnary of system partitions found with
            lsblk command and their attributes.
    """

    def __init__(self, master: py_cui.PyCUI):
        """Constructor for Parameters menu

        Args:
            master (py_cui.PyCUI): PyCUI constructor
        """

        self.master = master

        self.partition_to_search = None
        self.string_to_search = None
        self.partitions_dict = None

        LOGGER.write("info", "Starting 'ParametersView' CUI window")
        HELPER.is_user_root(window=self.master)

        self.create_ui_content()
        self.add_partitions_to_list()

    def create_ui_content(self):
        """Handles the creation of the UI elements."""

        self.partitions_list_scroll_menu = self.master.add_scroll_menu(
            "Select a partition to search:", 0, 0, row_span=9, column_span=5
        )
        self.partitions_list_scroll_menu.add_key_command(py_cui.keys.KEY_ENTER, self.select_partition)

        # Color rules
        self.partitions_list_scroll_menu.add_text_color_rule("Mounted at", py_cui.YELLOW_ON_BLACK, "contains")
        self.partitions_list_scroll_menu.set_selected_color(py_cui.GREEN_ON_BLACK)

        self.string_text_box = self.master.add_text_block("Enter a text to search:", 0, 5, row_span=9, column_span=5)

        self.confirm_search_button = self.master.add_button(
            "Start search",
            9,
            4,
            row_span=1,
            column_span=2,
            padx=0,
            pady=0,
            command=self.confirm_search,
        )

    def add_partitions_to_list(self):
        """Populates the partition list with lsblk output."""

        partitions_list = HELPER.lsblk()
        self.partitions_dict = HELPER.format_partitions_list(window=self.master, raw_lsblk=partitions_list)

        if self.partitions_dict is None:
            return

        for partition in self.partitions_dict:
            if self.partitions_dict[partition]["IS_MOUNTED"]:
                self.partitions_list_scroll_menu.add_item(
                    "Name: {name}  -  Type: {fstype}  -  Mounted at: {mountpoint}".format(
                        name=partition,
                        fstype=self.partitions_dict[partition]["FSTYPE"],
                        mountpoint=self.partitions_dict[partition]["MOUNT_POINT"],
                    )
                )
            else:
                self.partitions_list_scroll_menu.add_item(
                    "Name: {name}  -  Type: {fstype}".format(
                        name=partition, fstype=self.partitions_dict[partition]["FSTYPE"]
                    )
                )

            LOGGER.write(
                "debug",
                f"Partition added to list: {str(partition)}",
            )

    def select_partition(self):
        """Handles the user selection of a partition in the list."""

        selected_partition = re.findall(r"Name\:\ ([^\ \n]+)\ ", self.partitions_list_scroll_menu.get())[0]

        if self.partitions_dict[selected_partition]["IS_MOUNTED"]:
            # Warn the user to unmount his partition first
            self.master.show_warning_popup(
                "Warning",
                f"It is highly recommended to unmount {selected_partition} first.",
            )
        else:
            self.master.show_message_popup("", f"Partition {selected_partition} selected.")

        self.partition_to_search = "/dev/" + selected_partition.strip()

        LOGGER.write(
            "info",
            f"Partition selected: {self.partition_to_search}",
        )

    def confirm_search(self):
        """Checks if partition is selected and string is given.
        If all required elements are present, launch confirm_search function.
        """

        if not HELPER.is_user_root(window=self.master):
            return

        self.string_to_search = self.string_text_box.get()

        LOGGER.write("info", "Starting search")

        if self.partition_to_search == "":
            # No partition selected
            self.master.show_message_popup("Error", "You have to select a partition to search.")
            LOGGER.write("warning", "No partition selected for search")
        elif self.string_to_search.replace(" ", "").replace("\n", "").replace("\t", "") == "":
            # Blank string to search
            self.master.show_message_popup("Error", "You have to enter a text to search.")
            LOGGER.write("warning", "No string given for search")
        else:
            # Prompt to confirm string
            self.master.show_yes_no_popup(
                "Do you want to start searching this text on partition {partition} ?".format(
                    partition=self.partition_to_search
                ),
                self.start_search,
            )

    def start_search(self, is_confirmed: bool):
        """Closes parameters menu and open search menu if confirmed.

        Args:
            is_confirmed (bool): User popup selection
        """

        if is_confirmed:
            VIEWS_HANDLER.close_view_parameters()
            VIEWS_HANDLER.open_view_search(
                partition=self.partition_to_search,
                string_to_search=self.string_to_search.strip(),
            )