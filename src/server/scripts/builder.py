from django.template import Template, Context, Engine

from pprint import pformat
import os
import logging
import errno

# from server.settings.env import ROOT_DIR

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class ScriptBuilder(object):

    # Script template locations
    LOCATIONS = {
        "EQSANS": None,
        # "BioSANS": ROOT_DIR("../config/reduction/biosans.tpl"),
        # "GPSANS": ROOT_DIR("../config/reduction/gpsans.tpl"),
        "BioSANS": os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates", "biosans.tpl"),
        "GPSANS": os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates", "gpsans.tpl"),
    }

    def __init__(self, data, instrument, ipts, experiment=None):
        '''
        instrument, ipts, experiment :: are objects
        '''
        self.template_file_path = self.LOCATIONS[instrument.name]
        self.engine = Engine(
            # debug=True,
            builtins=['server.scripts.filters'], # this is for tags and filters
        )
        # Because the following is not part of the data
        data.update({
            "instrument_name": instrument.name,
            "ipts_number": ipts.number,
            "experiment_number": experiment.number,
            "data_file_path_template": instrument.data_file_path_template,
        })
        self.data = data
        self.instrument = instrument
        self.ipts = ipts
        self.experiment = experiment

        self.data.pop('script', None)
        logger.debug(pformat(self.data))

    def get_reduction_path(self):
        return self.instrument.reduction_path_template % self.data


    def build_script(self):
        '''
        Build a script from a template file @script_file_path,
        @data is a dictionary / json
        @return script as string
        '''
        # logger.debug(pformat(self.data))
        if not os.path.exists(self.template_file_path):
            logger.error("Template file %s does not exist.",
                         self.template_file_path)
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                self.template_file_path)
        script_filtered = ""
        if os.path.isfile(self.template_file_path):
            with open(self.template_file_path) as f:
                lines = f.readlines()
                # text = '\n'.join(lines)
                text = ''.join(lines)
                template = Template(
                    text,
                    engine=self.engine,
                )
                context = Context(self.data)
                try:
                    script = template.render(context)
                    # script_filtered = "\n".join([ll.rstrip() for ll in script.splitlines() if ll.strip()])
                except Exception as e:
                    raise e
                script_filtered = script
        else:
            logger.error("Template file %s does not exist!", self.template_file_path)
        return script_filtered



if __name__ == "__main__":
    print("START!")
    d = {
        'title': 'Reduction 5',
        'user': 'rhf'
    }
    d.update({"ipts":"12345"})
    script_builder = ScriptBuilder("BioSANS", d)
    res = script_builder.build_script()
    print(res)