from radkit_client import Device, run_on_device_dict
from radkit_common import nglog
import re
import json

IC = nglog.LazyTag("NXOS Neighbor Discovery", desc="Tag for Neighbor Discovery IC")
nglog.basicConfig()

def json_parser(commands,devices):
    # Generating "<cmd> | json | no-more"
    pipes = " | json | no-more"
    cmds = [s + pipes for s in commands]
    # Requesting commands from RADKit inventory
    request = devices.exec(cmds).wait()
    parsed_cmd_tmp = {}
    for dev in request.result:
        parsed_cmd_tmp[dev] = {}
        for cmd in request.result[dev]:
            if json_decoder(request.result[dev][cmd].data) is not None:
                tmp_json = json_decoder(request.result[dev][cmd].data)
                # Removing " | json | no-more" from show commands
                cmd = cmd.replace(" | json | no-more", "")
                parsed_cmd_tmp[dev][cmd] = {}
                parsed_cmd_tmp[dev][cmd] = tmp_json
            else:
                nglog.info("This command `" + cmd + "` has encountered error on device " + dev)
                cmd = cmd.replace(" | json | no-more", "")
                parsed_cmd_tmp[dev][cmd] = {}
                parsed_cmd_tmp[dev][cmd] = None
    return parsed_cmd_tmp

def json_decoder(output):
    output = output[output.find('{'):]
    output = re.sub('([^}]*)$','',output)
    test_output = output.replace('\n','')
    try:
        output_json = json.loads(test_output)
    except ValueError:
        output_json = None
        # Eventually if we would like to finish execution
        #sys.exit(1)
    return output_json

def space_check(device, parsed_cmd, path, border_value):
        devices = [item[0] for item in device.items()]
        nglog.info("Devices where checks are done: " + str(devices))
        for dev in devices:
            nglog.info("Device: " + dev)
            for item in parsed_cmd[dev]["show system internal flash"]["TABLE_flash"]["ROW_flash"]:
                if item["Mounted-on"] == path:
                    used_space = int(item["Use-percent"])
                    if used_space >= int(border_value): 
                        nglog.info("### NOT OK ### - " + item["Mounted-on"] + " | Used space: " + item["Use-percent"] + "%\n")
                    else:
                        nglog.info("### OK ### - " + item["Mounted-on"] + " | Used space: " + item["Use-percent"] + "%\n")

def get_commands(device : Device,*,path: str = "/bootflash",border_value: str = "5") -> None:
    device = device.filter("name","(fx3-).+")
    parsed_cmd = json_parser(["show system internal flash"],device)
    if len(path) > 0:
        space_check(device, parsed_cmd, path, border_value)
	
if __name__ == "__main__":
	run_on_device_dict(get_commands)