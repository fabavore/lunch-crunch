#   LunchCrunch: A Python desktop app to manage food ordering
#   Copyright (C) 2025  Fabian Sauer

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
import ttkbootstrap as ttk


DEFAULT_TEMPLATE = """Liebe:r Essenslieferant:in,

für unseren Kindergarten möchten wir heute {anzahl} Portionen Essen bestellen.

Mit besten Grüßen

Kindergarten Tierkinder"""

DEFAULT_GROUPS = ("Hasen", "Igel", "Rehkids")


def validate_number(x) -> bool:
    return x.isdigit() or x == ""


class NumberEntryFrame(ttk.Frame):
    def __init__(self, parent, values, title=None, width: int=4):
        super().__init__(parent)

        # Register validation callback
        validate = self.register(validate_number)

        if title is not None:
            self.title = ttk.Label(self, text=title)
            self.title.pack()

        self.entries_frame = ttk.Frame(self)
        self.entries_frame.pack()

        for i, (key, value) in enumerate(values.items()):
            label = ttk.Label(self.entries_frame, text=key)
            label.grid(row=i + 1, column=0, sticky="e")

            entry = ttk.Entry(self.entries_frame, width=width, textvariable=value,
                              validate="all", validatecommand=(validate, "%P"))
            entry.grid(row=i + 1, column=1, sticky="w")


class OrderFrame(ttk.Frame):
    def __init__(self, parent, groups):
        super().__init__(parent)

        self.template = DEFAULT_TEMPLATE
        self.orders = {g: ttk.IntVar() for g in groups}

        self.entries = NumberEntryFrame(self, self.orders, title="Bestellung")
        self.entries.pack()

        self.preview = ttk.Text(self, height=10, state="disabled")
        self.preview.pack()

        self.send_btn = ttk.Button(self, command=self.update_preview, text="Bestellung absenden")
        self.send_btn.pack()

        # Bind events for auto-updating the preview
        for _, value in self.orders.items():
            value.trace_add("write", lambda var, index, mode: self.update_preview())

        self.update_preview()

    def update_preview(self):
        try:
            total = sum([var.get() for _, var in self.orders.items()])

            self.preview.config(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", self.template.format(anzahl=total))
            self.preview.config(state="disabled")
        except Exception as e:
            print(f"Preview error: {e}")


class LunchOrderApp(ttk.Window):
    def __init__(self):
        super().__init__(title="🍎 Mittagessenbestellung")
        self.geometry("800x600")

        self.notebook = ttk.Notebook(self, padding=10)
        self.notebook.pack(fill="both", expand=True)

        order_frame = OrderFrame(self.notebook, groups=DEFAULT_GROUPS)
        self.notebook.add(order_frame, text="🍴 Bestellung")

        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Einstellungen")

    def on_closing(self):
        print("closing...")
        self.destroy()

    def run(self):
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()


def main():
    app = LunchOrderApp()
    app.run()


if __name__ == "__main__":
    main()
