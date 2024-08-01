import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QSizePolicy
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optomo")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QGridLayout(self.central_widget)

        self.vtk_widgets = []
        self.reslices = []
        self.lines = []
        self.states = []

        for i in range(3):
            vtk_widget, reslice = self.create_vtk_panel(i)
            self.vtk_widgets.append(vtk_widget)
            self.reslices.append(reslice)
            row, col = divmod(i, 2)
            layout.addWidget(vtk_widget, row, col)

        vtk_widget = self.create_vtk_panel_for_volume_rendering()
        self.vtk_widgets.append(vtk_widget)
        layout.addWidget(vtk_widget, 1, 1)

        self.show()

    def create_vtk_panel(self, panel_index):
        vtk_widget = QVTKRenderWindowInteractor(self.central_widget)
        vtk_widget.setMinimumSize(450, 450)
        vtk_widget.setMaximumSize(450, 450)
        vtk_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        vtk_widget.AddObserver("MouseWheelForwardEvent", lambda obj, ev, i=panel_index: self.apply_update(i, 1))
        vtk_widget.AddObserver("MouseWheelBackwardEvent", lambda obj, ev, i=panel_index: self.apply_update(i, -1))

        vtk_widget.Initialize()
        vtk_widget.Start()
        reslice = self.add_vtk_components(vtk_widget.GetRenderWindow(), panel_index)

        return vtk_widget, reslice

    def create_vtk_panel_for_volume_rendering(self):
        vtk_widget = QVTKRenderWindowInteractor(self.central_widget)
        vtk_widget.setMinimumSize(450, 450)
        vtk_widget.setMaximumSize(450, 450)
        vtk_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        vtk_widget.Initialize()
        vtk_widget.Start()

        self.add_vtk_components_for_volume_rendering(vtk_widget.GetRenderWindow())

        return vtk_widget

    def add_vtk_components(self, render_window, panel_index):
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName("C:/Users/fatil/OneDrive/Belgeler/Dicoms/beyin")
        reader.Update()

        extent = reader.GetDataExtent()
        spacing = reader.GetOutput().GetSpacing()
        origin = reader.GetOutput().GetOrigin()

        center = [
            origin[0] + spacing[0] * 0.5 * (extent[0] + extent[1]),
            origin[1] + spacing[1] * 0.5 * (extent[2] + extent[3]),
            origin[2] + spacing[2] * 0.5 * (extent[4] + extent[5])
        ]

        reslice = vtk.vtkImageReslice()
        reslice.SetInputConnection(reader.GetOutputPort())
        reslice.SetOutputDimensionality(2)
        reslice.SetResliceAxesOrigin(center)
        new_extent = (0, 449, 0, 449, 0, 0)
        reslice.SetOutputExtent(new_extent)

        # Yeni spacing değerlerini hesapla ve ayarla
        if panel_index == 0:  # X ekseni
            new_spacing = (spacing[0] * (extent[1] - extent[0] + 1) / 450,
                           spacing[2] * (extent[5] - extent[4] + 1) / 450,
                           spacing[1])
        elif panel_index == 1:  # Y ekseni
            new_spacing = (spacing[1] * (extent[3] - extent[2] + 1) / 450,
                           spacing[2] * (extent[5] - extent[4] + 1) / 450,
                           spacing[0])
        elif panel_index == 2:  # Z ekseni
            new_spacing = (spacing[0] * (extent[1] - extent[0] + 1) / 450,
                           spacing[1] * (extent[3] - extent[2] + 1) / 450,
                           spacing[2])

        reslice.SetOutputSpacing(new_spacing)

        state = 225

        line_source1 = vtk.vtkLineSource()
        line_source1.SetPoint1(0, state, 0)
        line_source1.SetPoint2(450, state, 0)

        line_source2 = vtk.vtkLineSource()
        line_source2.SetPoint1(state, 0, 0)
        line_source2.SetPoint2(state, 450, 0)

        self.states.append(state)
        self.states.append(state)

        line_mapper1 = vtk.vtkPolyDataMapper2D()
        line_mapper1.SetInputConnection(line_source1.GetOutputPort())

        line_actor1 = vtk.vtkActor2D()
        line_actor1.SetMapper(line_mapper1)

        line_mapper2 = vtk.vtkPolyDataMapper2D()
        line_mapper2.SetInputConnection(line_source2.GetOutputPort())

        line_actor2 = vtk.vtkActor2D()
        line_actor2.SetMapper(line_mapper2)

        if panel_index == 0:
            reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 0, 1, 0, 1, 0)  # Y ekseni
            line_actor1.GetProperty().SetColor(0, 0, 1)
            line_actor2.GetProperty().SetColor(1, 0, 0)
        elif panel_index == 1:
            reslice.SetResliceAxesDirectionCosines(0, 1, 0, 0, 0, 1, 1, 0, 0)  # X ekseni
            line_actor1.GetProperty().SetColor(0, 0, 1)
            line_actor2.GetProperty().SetColor(0, 1, 0)
        elif panel_index == 2:
            reslice.SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1)  # Z ekseni
            line_actor1.GetProperty().SetColor(0, 1, 0)
            line_actor2.GetProperty().SetColor(1, 0, 0)

        mapper = vtk.vtkImageMapper()
        mapper.SetInputConnection(reslice.GetOutputPort())
        mapper.SetColorWindow(100)
        mapper.SetColorLevel(50)

        actor = vtk.vtkActor2D()
        actor.SetMapper(mapper)

        self.lines.append(line_source1)
        self.lines.append(line_source2)

        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.AddActor(line_actor1)
        renderer.AddActor(line_actor2)
        renderer.SetBackground(0.1, 0.2, 0.4)

        render_window.AddRenderer(renderer)
        render_window.Render()

        return reslice

    def add_vtk_components_for_volume_rendering(self, render_window):
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName("C:/Users/fatil/OneDrive/Belgeler/Dicoms/beyin")
        reader.Update()

        volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        volumeMapper.SetInputConnection(reader.GetOutputPort())

        volumeColor = vtk.vtkColorTransferFunction()
        volumeColor.AddRGBPoint(0, 0.0, 0.0, 0.0)
        volumeColor.AddRGBPoint(35, 1.0, 0.5, 0.5)
        volumeColor.AddRGBPoint(60, 1.0, 0.5, 0.5)
        volumeColor.AddRGBPoint(100, 1.0, 1.0, 0.9)

        volumeScalarOpacity = vtk.vtkPiecewiseFunction()
        volumeScalarOpacity.AddPoint(0, 0.00)
        volumeScalarOpacity.AddPoint(35, 0.1)
        volumeScalarOpacity.AddPoint(60, 0.1)
        volumeScalarOpacity.AddPoint(100, 0.80)

        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(volumeColor)
        volumeProperty.SetScalarOpacity(volumeScalarOpacity)

        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

        renderer = vtk.vtkRenderer()
        renderer.AddVolume(volume)

        render_window.AddRenderer(renderer)
        render_window.Render()

    def apply_update(self, panel_index, direction):
        reslice = self.reslices[panel_index]
        center = list(reslice.GetResliceAxesOrigin())
        spacing = reslice.GetOutputSpacing()

        if panel_index == 0:  # X ekseni
            center[1] += direction * spacing[1]
            self.states[3] += direction * spacing[1]
            self.lines[3].SetPoint1(self.states[3], 0, 0)
            self.lines[3].SetPoint2(self.states[3], 450, 0)
            self.states[4] += direction * spacing[1]
            self.lines[4].SetPoint1(0, self.states[4], 0)
            self.lines[4].SetPoint2(450, self.states[4], 0)
        elif panel_index == 1:  # Y ekseni
            center[0] += direction * spacing[0]
            self.states[1] += direction * spacing[0]
            self.lines[1].SetPoint1(self.states[1], 0, -5)
            self.lines[1].SetPoint2(self.states[1], 450, -5)
            self.states[5] += direction * spacing[0]
            self.lines[5].SetPoint1(self.states[5], 0, -5)
            self.lines[5].SetPoint2(self.states[5], 450, -5)
        elif panel_index == 2:  # Z ekseni
            center[2] += direction * spacing[2]
            self.states[0] += direction * spacing[2]
            self.lines[0].SetPoint1(0, self.states[0], -5)
            self.lines[0].SetPoint2(450, self.states[0], -5)
            self.states[2] += direction * spacing[2]
            self.lines[2].SetPoint1(0, self.states[2], -5)
            self.lines[2].SetPoint2(450, self.states[2], -5)

        reslice.SetResliceAxesOrigin(center)
        reslice.Update()

        for vtk_widget in self.vtk_widgets:
            vtk_widget.GetRenderWindow().Render()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
