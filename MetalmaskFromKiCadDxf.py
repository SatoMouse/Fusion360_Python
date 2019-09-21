import adsk.core, adsk.fusion, traceback, math

def run(context):
  ui = None
  MetalMaskMin = 100
  MetalMaskMax = 150
  try:
    app = adsk.core.Application.get()
    ui  = app.userInterface
    importManager = app.importManager
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    root = design.rootComponent

    title = 'Import DXF'
    if not design:
      ui.messageBox('No active Fusion design', title)
      return

    # Show dialog to select DXF files
    dlg = ui.createFileDialog()
    dlg.isMultiSelectEnabled = True
    dlg.title = 'Open DXF File'
    dlg.filter = 'Comma Separated Values (*.dxf);;All Files (*.*)'
    if dlg.showOpen() != adsk.core.DialogResults.DialogOK :
      return
    
    # Import DXF
    filenamesOther = []
    for filename in dlg.filenames:
      if filename.find('-Edge_Cuts') != -1:
        dxfOptions = importManager.createDXF2DImportOptions(filename, root.xYConstructionPlane)
        dxfOptions.isViewFit = False
        importManager.importToTarget(dxfOptions, root)
      else:
        filenamesOther.append(filename)
    for filename in filenamesOther:
      dxfOptions = importManager.createDXF2DImportOptions(filename, root.xYConstructionPlane)
      dxfOptions.isViewFit = False
      importManager.importToTarget(dxfOptions, root)

    sketch = root.sketches.item(0)
    skt = root.sketches.item(1)
    isFirst = True
    metalMaskX = 0.0
    metalMaskY = 0.0

    # Find board size
    for curve in sketch.sketchCurves:
      ptStart = curve.startSketchPoint.geometry
      ptEnd = curve.endSketchPoint.geometry
      if isFirst:
        maxX =  ptStart.x
        minX =  ptStart.x
        maxY =  ptStart.y
        minY =  ptStart.y
      if ptStart.x > maxX:
        maxX =  ptStart.x
      if ptEnd.x > maxX:
        maxX =  ptEnd.x
      if  ptStart.x < minX:
        minX =  ptStart.x
      if  ptEnd.x < minX:
        minX =  ptEnd.x
      if  ptStart.y > maxY:
        maxY =  ptStart.y
      if  ptEnd.y > maxY:
        maxY =  ptEnd.y
      if  ptStart.y < minY:
        minY =  ptStart.y
      if  ptEnd.y < minY:
        minY =  ptEnd.y
      isFirst = False

    # Draw MetalMaskOutline
    lenX = maxX - minX
    lenY = maxY - minY

    if lenX >= lenY:
      metalMaskX = MetalMaskMax / 10
      metalMaskY = MetalMaskMin / 10
    else:
      metalMaskX = MetalMaskMin / 10
      metalMaskY = MetalMaskMax / 10

    centerX = (maxX + minX) / 2
    centerY = (maxY + minY) / 2

    ptXmin = centerX - metalMaskX / 2
    ptXmax = centerX + metalMaskX / 2
    ptYmin = centerY - metalMaskY / 2
    ptYmax = centerY + metalMaskY / 2

    pt1 = adsk.core.Point3D.create(ptXmin, ptYmin, 0)
    pt2 = adsk.core.Point3D.create(ptXmax, ptYmin, 0)
    pt3 = adsk.core.Point3D.create(ptXmax, ptYmax, 0)
    pt4 = adsk.core.Point3D.create(ptXmin, ptYmax, 0)

    sketchLines = skt.sketchCurves.sketchLines
    firstLine = sketchLines.addByTwoPoints(pt1, pt2)
    lastLine = firstLine
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint, pt3)
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint, pt4)
    lastLine = sketchLines.addByTwoPoints(lastLine.endSketchPoint, firstLine.startSketchPoint)

    # Find Large area profile
    index = 0
    maxArea = 0.0
    indexMax = 0
    for profile in skt.profiles:
      area = profile.areaProperties(adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy).area
      if area > maxArea:
        maxArea = area
        indexMax = index
      index+= 1
    profLarge = skt.profiles[indexMax]
    
    # Create body
    extrudes = root.features.extrudeFeatures
    extInput = extrudes.createInput(profLarge, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(-0.01)
    extInput.setDistanceExtent(False, distance)
    extrudes.add(extInput)
  except:
    if ui:
      ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))