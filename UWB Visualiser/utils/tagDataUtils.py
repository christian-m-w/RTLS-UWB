from tagData import TagData, AnchorPosition, TagPosition

class TagDataUtils():
    def serial_toTagData(self, row):
        t = TagData()
        t.TimeStamp = row[0]

        # AN0,4818,0.65,2.49,2.10,1.93
        t.AnchorPositions = []
        t.AnchorPositions.append(AnchorPosition(row[4], float(row[5]), float(row[6]), float(row[7]), float(row[8])))
        t.AnchorPositions.append(AnchorPosition(row[10], float(row[11]), float(row[12]), float(row[13]), float(row[14])))
        t.AnchorPositions.append(AnchorPosition(row[16], float(row[17]), float(row[18]), float(row[19]), float(row[20])))

        # POS,1.83,3.33,2.16,47
        if row[2] == "4": # Check number of anchors in position calculation (3 or 4)
            t.AnchorPositions.append(AnchorPosition(row[22], float(row[23]), float(row[24]), float(row[25]), float(row[26])))
            t.TagPosition = TagPosition(float(row[28]), float(row[29]), float(row[30]), int(row[31]))
        else:
            t.TagPosition = TagPosition(float(row[22]), float(row[23]), float(row[24]), int(row[25]))

        return t
    
    def csv_toTagData(self, row):
        t = TagData()
        t.TimeStamp = row[0]

        # 4818,0.65,2.49,2.10,1.93
        t.AnchorPositions = []
        t.AnchorPositions.append(AnchorPosition(row[2], float(row[3]), float(row[4]), float(row[5]), float(row[6])))
        t.AnchorPositions.append(AnchorPosition(row[7], float(row[8]), float(row[9]), float(row[10]), float(row[11])))
        t.AnchorPositions.append(AnchorPosition(row[12], float(row[13]), float(row[14]), float(row[15]), float(row[16])))

        # POS,1.83,3.33,2.16,47
        if row[1] == "4": # Check number of anchors in position calculation (3 or 4)
            t.AnchorPositions.append(AnchorPosition(row[17], float(row[18]), float(row[19]), float(row[20]), float(row[21])))
            t.TagPosition = TagPosition(float(row[22]), float(row[23]), float(row[24]), int(row[25]))
        else:
            t.TagPosition = TagPosition(float(row[17]), float(row[18]), float(row[19]), int(row[20]))

        return t
    
    def tagData_ToCSV(self, td: TagData):
        anchorPositions = ""
        for ap in td.AnchorPositions:
            anchorPositions += f"{ap.AnchorID},{ap.X},{ap.Y},{ap.Z},{ap.MetersFromTag},"
        
        csvLine = f"{td.TimeStamp},{len(td.AnchorPositions)},{anchorPositions}{td.TagPosition.X},{td.TagPosition.Y},{td.TagPosition.Z},{td.TagPosition.QF}"
        return csvLine