from ctypes import resize
from multiprocessing.sharedctypes import Value
import mset
import os.path
import time
import itertools
import random
from operator import index, itemgetter

#Create Main Window
mainUI = mset.UIWindow("Iteration Renderer_V5")
mainUI.width= 500

drawer = mset.UIDrawer(name="Help")
helpWindow = mset.UIWindow(name="Drwe")
drawer.containedControl = helpWindow

# HELP UI DRAWER
explainText00 = mset.UILabel("Mark the folders that have to be randomized, with the suffix \"_folder\"")
explainText01 = mset.UILabel("for I.E : \"Weapons_folder\" - Case sensitive")
explainText02 = mset.UILabel("When enabling rarity an extra underscore with a integer digit representing drop ")
explainText03 = mset.UILabel("chance should be added")
helpWindow.addElement(explainText00)
helpWindow.addReturn()
helpWindow.addElement(explainText01)
helpWindow.addReturn()
helpWindow.addElement(explainText02)
helpWindow.addReturn()
helpWindow.addElement(explainText03)

scrollbox = mset.UIScrollBox()
scrollbox_window = mset.UIWindow(name="Scrollbox Window")
scrollbox.containedControl = scrollbox_window
scrollbox_window.addElement(drawer)



renderRangeMin = mset.UISliderInt(min=1,max=1,name="Min")
renderRangeMax = mset.UISliderInt(min=1,max=1,name="Max")
renderRangeMax.value = 1

#Get all objects in scene

allObjects  = mset.getAllObjects()
cameraObject = mset.CameraObject
initialized = False
raritySet = False
combs = []

#Lists For UI
ignorelist = []
folderIgnoreListFunc = []
folderIgnoreList = mset.UIListBox("Folder To ignore")
folderInput = mset.UISliderInt(min=1, max=6, name="Folder Amount")
checkerbox = mset.UICheckBox()

def startUpVisibility(all):
	global pstState,childVis
	pstState = {}
	childVis = {}
	for	object in all:
		pstState[object.name] = object.visible
		
		CurChildVis = []
		for child in object.getChildren():
			CurChildVis.append(child.visible)
	
	childVis[object.name] = CurChildVis  
	#print(f"Object: {object.name} set to {object.visible}")

def recoverVisibility():
	all = mset.getAllObjects()
	for object in all :
		if object.name in pstState.keys():
			#print(f"object: {object.name} found in dict")
			object.visible = pstState[object.name]
		else:
			print(f"Object: {object.name} visibility could not be recovered")

		if object.name in childVis.keys():
			for child in object.getChildren():
				child.visible = childVis[object.name][object.getChildren().index(child)]

# Function to shuffle a list according to the given order of elements
def Shuffle(nums, pos):
 
    # create an auxiliary space of size `n`
    aux = [None] * len(nums)
 
    # fill the auxiliary space with the correct order of elements
    for i, e in enumerate(pos):
        aux[e] = nums[i]
 
    # copy the auxiliary space back to the given list
    for i in range(len(nums)):
        nums[i] = aux[i]

def PushIgnoredItems():
	if folderIgnoreList.selectedItem != None and  (len(folderObjects)-len(ignorelist)>=2) :
		print(len(folderObjects))
		ignorelist.append(folderIgnoreListFunc[folderIgnoreList.selectedItem])
		print("ingored Group: " + folderIgnoreListFunc[folderIgnoreList.selectedItem])
	else:
		print("COULD NOT REMOVE LAST GROUP")
	UpdateType()

def ClearIgnoredFolders():
	ignorelist.clear()
	UpdateType()

#get all objects of type
def UpdateType():
	global initialized
	allObjects  = mset.getAllObjects()
	startUpVisibility(allObjects)
	initialized=True
	folderIgnoreListFunc.clear()
	folderIgnoreList.clearItems()
	global folderObjects
	folderObjects = []
	folderObjectsNames = []
	global childrenOfFolders
	childrenOfFolders = []
	
	# number of times element exists in list
	# Get Folders that are defined by _folder
	for object in allObjects:
		#if isinstance(object, mset.SubMeshObject): 
			objectname = object.name
			if "folder" in objectname:
				folderObjects.append(object)
				folderObjectsNames.append(object.name)
				print("Added Folder: "+ object.name)

			if isinstance(object,mset.CameraObject):
				global cameraObject
				cameraObject = object
				#print("Added Camera: " + object.name)

			if isinstance(object,mset.SkyBoxObject):
				global skybox
				skybox = object

	UpdateFolderObject()
	#CalculateCombinations()
	
	if raritySet:
		CheckRarity()
	else:
		CalculateCombinations()

def UpdateFolderObject():
	#Get children and promote to childrenarray
	for object in folderObjects:
		if object is not None:
			if ignorelist.count(object.name)==0:
				folderIgnoreList.addItem(object.name)
				folderIgnoreListFunc.append(object.name)
				childrenOfFolders.append(object.getChildren())
				#print("Added Children of " + object.name + " to the List")

def CalculateCombinations():
	global combs
	combs = list(itertools.product(*childrenOfFolders))
	renderAmountText.text = "Iterations Rendered: " + str(len(combs))
	renderRangeMax.max = len(combs)
	renderRangeMin.max = len(combs)
	checkValueInrange(renderRangeMax)

def CheckRarity():
	global weightedCombinations
	global combs
	global points
	combs = list(itertools.product(*childrenOfFolders))
	renderAmountText.text = "Iterations Rendered: " + str(len(combs))
	renderRangeMax.max = len(combs)
	renderRangeMin.max = len(combs)
	checkValueInrange(renderRangeMax)
	weightedCombinations = {}
	percentedCombinations = {}
	for comb in combs:
		index = combs.index(comb)
		points = 0
		for item in comb:
			try:
				x = item.name.split("_",1)
				point = int(x[1])
				points += point
			except Exception:
				pass	
		weightedCombinations[comb] = points
			
	maxsum = max(weightedCombinations.values())
	for comb in combs:
		percentage = (int((weightedCombinations[comb]/maxsum)*100))
		percentedCombinations[comb] = percentage
	
	percentedCombinations = sorted(percentedCombinations.items(), key=itemgetter(1))
	combs = list(dict(percentedCombinations).keys())
	points = list(dict(percentedCombinations).values())

#create array with all the possible combinations
def RenderAllCombinations():
	if initialized:
		renName = renderName.value
		#Render out each combination and print out the iteration, It will not create duplicates 
		for index in range(renderRangeMin.value-1,renderRangeMax.value):
			#Set all Childs to False Visibility
			for child in childrenOfFolders:
				for object in child:
					object.visible = False

			# Display the items in the combination
			for item in combs[index]:
				item.visible = True
				print(item.name)

			if raritySet:
				imagename = renName + "_" + str(index+1)+"_"+str(points[index])+".png"
			else:
				imagename = renName + "_" + str(index+1)+".png"
			
			#Render	Out the Combinations
			destpath = objectPath.value + imagename
			mset.renderCamera(path=destpath,width=-1,height=-1,sampling=-1,transparency=True,camera=cameraObject.name)				
			print("Render iteration:  " + str(index) + "out of: " + str(len(combs)-1))
			mset.freeUnusedResources()
			make_visible()
	else:
		UpdateType()

#DefineUI Elements
hideButton = mset.UIButton("Hide-Objects")
showAllButton = mset.UIButton("Show All")
inputlabel = mset.UILabel("Mesh To Ignore")
ignoreModel = mset.UITextField("ObjectsToignore")

#unhide all object of Type
def UnhideAll():
	for object in folderObjects:
		object.visible = True

#get folder functionality
def get_material_folder():
    path = mset.showOpenFolderDialog()
    if path != '':
        objectPath.value = path

def make_visible():
	for child in childrenOfFolders:
		for object in child:
			object.visible = True

def check_slider_max():
	if renderRangeMax.value < renderRangeMin.value: 
		renderRangeMax.value = renderRangeMin.value 
	
def check_slider_min():
	if renderRangeMin.value > renderRangeMax.value: 
		renderRangeMin.value = renderRangeMax.value 

def checkValueInrange(slider):
	if slider.value > slider.max:
		slider.value = slider.max

def checkButtonValue():
	global raritySet
	raritySet = checkerbox.value
	UpdateType()

def closePlugin():
	lambda: mset.shutdownPlugin()

#Creation UI
#Base UI
closeButton = mset.UIButton("Close")
updateIgnoreButton = mset.UIButton("Ignore")
clearIgnoresButton = mset.UIButton("Clear")
refreshButton = mset.UIButton("Initialize Scene")
renderAmountText = mset.UILabel("")
renderButton = mset.UIButton("Render All")
unhideAllButton = mset.UIButton("Unhide-Objects")
showAll = mset.UIButton("ShowAll")
folderText = mset.UILabel("Folder to Render to:")
objectPath = mset.UITextField()
objectPath.value  = ""
backgroundText = mset.UILabel("Enable Background")

imageText = mset.UILabel("ImageName")
renderName = mset.UITextField()
renderName.value  = "Placeholder"

#UI For Help

closeButton = mset.UIButton("Close")
recoverVisButton = mset.UIButton("Recover visibility")
picker = mset.UIColorPicker("Color")
checkerBoxText = mset.UILabel("Enable Rarity")


#UI Functionality
renderButton.onClick = RenderAllCombinations
showAllButton.onClick = make_visible
refreshButton.onClick = UpdateType
updateIgnoreButton.onClick =  PushIgnoredItems
clearIgnoresButton.onClick = ClearIgnoredFolders
recoverVisButton.onClick = recoverVisibility
closeButton.onClick = lambda: mset.shutdownPlugin()
renderRangeMax.onChange = check_slider_max
renderRangeMin.onChange = check_slider_max
checkerbox.onChange = checkButtonValue

#Add buttons
mainUI.addElement(refreshButton)
mainUI.addSpace(5)
mainUI.addElement(checkerBoxText)
mainUI.addElement(checkerbox)
mainUI.addReturn()
mainUI.addElement(folderIgnoreList)
mainUI.addElement(updateIgnoreButton)
mainUI.addElement(clearIgnoresButton)
mainUI.addReturn()
mainUI.addElement(renderRangeMin)
mainUI.addReturn()
mainUI.addElement(renderRangeMax)
mainUI.addReturn()

mainUI.addElement(imageText)
mainUI.addElement(renderName)
mainUI.addReturn()
mainUI.addElement(folderText)
mainUI.addElement(objectPath)

#UI Folder button
file_button = mset.UIButton("...")
file_button.onClick = get_material_folder
mainUI.addElement(file_button)

mainUI.addReturn()

mainUI.addReturn()
mainUI.addElement(renderButton)
mainUI.addElement(showAllButton)
mainUI.addReturn()
mainUI.addElement(renderAmountText)
mainUI.addReturn()
mainUI.addElement(scrollbox)
mainUI.addReturn()
mainUI.addElement(closeButton)
mainUI.addSpace(310)
mainUI.addElement(recoverVisButton)
