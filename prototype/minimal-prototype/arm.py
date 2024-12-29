from utils import *
import random
import pefile
import mmap
import hashlib
import string
import sys

class Arm:
    """A class that represents an arm of the bandit. An arm is a specific action that can be taken by the bandit.
    """
    def __init__(self, idx):
        """init function for Arm

        Args:
            idx (int): index of the arm
        """
        self.idx = idx
        self.action = None
        self.content = None
        self.description = None
        self.list_reward = []
        self.n_play = 0

    def update_description(self):
        """function to update the description of the arm/action
        """
        self.description = self.action

    def pull(self, sample):
        """function to pull the arm
        currently only increments the pull count

        Args:
            sample (Sample): The sample to pull the arm on

        Returns:
            _type_: _description_
        """
        logger_rew.info('pull Arm %s (%d)' %(self.description, self.idx))
        sample.pull_count += 1
        # TODO: can this be removed? the function is not implemented
        return self.transfer(sample.current_exe_path, rewriter_output_folder)
    
    # TODO: can this be removed since it is not implemented?
    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """not implemented yet

        Args:
            input_path (_type_): _description_
            output_folder (_type_, optional): _description_. Defaults to rewriter_output_folder.
            verbose (bool, optional): _description_. Defaults to True.

        Raises:
            Exception: _description_
        """
        raise Exception ('Not Implemented')

    def estimated_probas(self):
        """not implemented yet
        TODO: can this be removed?

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError

    def get_output_path(self, folder, input_path):
        """function to get the path of a new modification of a sample

        Args:
            folder (path): Folder the file is in
            input_path (path): path the file is currently at (will only use basename)

        Returns:
            path: Path the new modified file will be at
        """
        return folder + basename(input_path) + '.' + self.action

    def get_overlay_size(self, sample_path):
        """_summary_function to get the size of the overlay data in a PE file

        Args:
            sample_path (path): Path to the file the overlay data should be extracted from

        Returns:
            int: size of the overlay data
        """
        # get sample size
        file_size = os.path.getsize(sample_path)
        # try to parse the PE file
        pe = self.try_parse_pe(sample_path)
        # if parsing fails, return 0
        if pe == None:
            logger_rew.info('action fail, no change')
            return 0
        # get the offset of the overlay data
        overlay_offset = pe.get_overlay_data_start_offset()
        overlay_size = 0
        # if there is overlay data, calculate the size
        if overlay_offset != None:
            overlay_size = file_size - overlay_offset
        return overlay_size

    def try_parse_pe(self, sample_path):
        """function to parse a PE file with pefile and return the PE object

        Args:
            sample_path (path): Path to the sample

        Returns:
            PE: The pefile.PE object
        """
        # try to parse pe, else throw exception
        try:
            pe = pefile.PE(sample_path)
            return pe
        except Exception as e:
            logger_rew.info('pefile parse fail')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger_rew.error('%s %s:%s cannot parse pe' %(exc_type, fname, exc_tb.tb_lineno))

    def get_available_size_safe(self, pe, section_idx):
        """Function to get the available size in a section of a PE file that will not break the file

        Args:
            pe (PE): The pe file object
            section_idx (int): index of the section

        Returns:
            int: Size of the available space
        """
        # get the section
        target_section = pe.sections[section_idx]
    
        # if section is not the last section
        if section_idx < len(pe.sections) - 1:
            # calculate the available size
            available_size = (pe.sections[section_idx+1].PointerToRawData - target_section.PointerToRawData) - target_section.Misc_VirtualSize
        
        # section is the last section in the file
        else:
            # get overlay data offset   
            overlay_offset = pe.get_overlay_data_start_offset()
            # pe has overlay data, calculate available size
            if overlay_offset != None:      
                available_size = (overlay_offset - target_section.PointerToRawData) - target_section.Misc_VirtualSize
            # no overlay data, get available size
            else:
                available_size = self.get_available_size(pe, section_idx)

        # if available size is not in the range of 0x1000, set to 0
        if available_size > 0x1000 or available_size < 0:
            available_size = 0
        # return size
        return available_size

    def get_available_size(self, pe, section_idx):
        """function to get the available size in a section of a PE file without any safety checks

        Args:
            pe (PE): The pe file object
            section_idx (int): Index of the section

        Returns:
            int: Size of the available space
        """
        # get target section
        target_section = pe.sections[section_idx]
        # calculate size
        available_size = target_section.SizeOfRawData - target_section.Misc_VirtualSize
        # no negative size possible
        if available_size < 0:
            available_size = 0
        # return size
        return available_size

    def print_section_names(self, pe):
        """function to print all section names of a PE file

        Args:
            pe (PE): The pefile.PE object the sections should be printed from
        """
        logger_rew.info(self.get_section_name_list(pe))

    def get_section_name_list(self, pe):
        """function to get a list of section names of a PE file

        Args:
            pe (PE): The pe file object

        Returns:
            list: List of section names
        """
        return [str(section.Name.split(b'\0',1)[0]).split('\'')[1] for section in pe.sections]


    def zero_out_file_content(self, file_path, offset, segment_size):
        """_summary_function to zero out a segment of a file and move the old data to a offset

        Args:
            file_path (path): Path to the file
            offset (int): Offset to move the old data to
            segment_size (int): Size of the segment to zero out
        """
        # creae zero payload
        content = ('\x00'*(segment_size)).encode()
        # open file for reading
        fp_in = open(file_path, 'rb')
        # get old file content
        file_content = fp_in.read()
        fp_in.close()

        # open file for writing
        fp_out = open(file_path, 'wb')
        # write the old file content to the offset
        fp_out.write(file_content[:offset])
        # write the zero payload to the segment
        fp_out.write(content)
        fp_out.write(file_content[offset + len(content):])
        fp_out.close()
    
    def align(self, val_to_align, alignment):
        """function to align a value to a specific alignment

        Args:
            val_to_align (int): value to align
            alignment (int): alignment

        Returns:
            int: the aligned value
        """
        return (int((val_to_align + alignment - 1) / alignment)) * alignment

class ArmOA(Arm):
    """class for the OA arm, which appends data to the overlay of a PE file

    Args:
        Arm (arm): The arm class
    """
    def __init__(self, idx, content=None):
        super().__init__(idx)
        # optional specific content to add
        self.content = content
        # if content if set and only one byte, set action to OA1
        if content and len(content) == 1:
            self.action = 'OA1'
        # else set action to OA/OA+Rand
        else:
            self.action = 'OA'
        # update the description
        self.update_description()

    def update_description(self):
        """function to update the description of the arm and determine wich OA is beeing used
        """
        # no content given -> generate random content
        if self.content == None:
            self.description = 'OA+Rand'
        # content given and only one byte -> set description to OA+1
        elif len(self.content) == 1:
            self.description = 'OA+1'
        # content given -> set description to OA+hash(content)
        else:
            self.description = 'OA+' + hashlib.md5(self.content).hexdigest()[:8]

    def set_content(self, content):
        """function to set the content of the arm

        Args:
            content (?): data to add as content
        """
        self.content = content
        if len(content) == 1:
            self.action = 'OA1'
        self.update_description()

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the arm to a sample

        Args:
            input_path (path): path of the input sample
            output_folder (path, optional): Path t owrite the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): If output should be verbose. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # copy the input file to the output path
        os.system('cp -p %s %s' %(input_path, output_path))
        # no content given -> generate random content
        if self.content == None:
            if verbose == True:
                logger_rew.info('generating new random content')
            _, _, self.content = Utils.get_random_content()
        if verbose == True:
            logger_rew.info('using arm idx: %d, len content: %d' %(self.idx, len(self.content)))
        # write content to the end of the file
        with open(output_path, 'ab') as f:
            f.write(self.content)
        
        # verify action changes
        old_overlay_size = self.get_overlay_size(input_path)
        new_overlay_size = self.get_overlay_size(output_path)

        if verbose == True:
            logger_rew.info('old overlay size: %d, new overlay size: %d' %(old_overlay_size, new_overlay_size))
        # return the path of the new sample
        return output_path

class ArmRD(Arm):
    """The RD arm class, which removes the debug data from a PE file

    Args:
        Arm (_type_): _description_
    """
    def __init__(self, idx):
        """init function for RD arm

        Args:
            idx (int): index of the arm
        """
        super().__init__(idx)
        # set action and description
        self.action = 'RD'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the RD arm to a sample

        Args:
            input_path (path): path to the input sample
            output_folder (path, optional): Path t owrite the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): If output should be verbose. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # create pe object
        pe = pefile.PE(input_path)
        segment_size = 0
        # iterate over the data directories
        for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
            # if the data directory is the debug directory
            if d.name == 'IMAGE_DIRECTORY_ENTRY_DEBUG':
                if verbose == True: 
                    logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
                # if data is present in debug directory
                if d.Size > 0:
                    # parse the debug directory
                    debug_directories = pe.parse_debug_directory(d.VirtualAddress, d.Size)
                    # iterate over the debug directories
                    if debug_directories:
                        for debug_directory in debug_directories:
                            # get the debug type
                            debug_type = debug_directory.struct.Type
                            # if the debug type is CodeView Debug Directory Entry (type 2)
                            if debug_type == 2:
                                # set the file offset and segment size
                                file_offset = debug_directory.struct.PointerToRawData
                                segment_size = debug_directory.struct.SizeOfData
                    d.VirtualAddress = 0
                    d.Size = 0
        # write the pe object to the output path
        pe.write(output_path)

        # if segment size is greater than 0, zero out the data
        if segment_size > 0:
            # set_bytes_at_offset doesn't take effect, zero out directly.
            self.zero_out_file_content(output_path, file_offset, segment_size)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
                if d.name == 'IMAGE_DIRECTORY_ENTRY_DEBUG':
                    if verbose == True: 
                        logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
        else:
            if verbose == True: 
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))

        return output_path

class ArmRC(Arm):
    """The RC arm class, which removes the signature from a PE file

    Args:
        Arm (_type_): _description_
    """
    def __init__(self, idx):
        """init function for RC arm

        Args:
            idx (int): index of the arm
        """
        super().__init__(idx)
        self.action = 'RC'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the RC arm to a sample

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)

        # create pe object
        pe = pefile.PE(input_path)
        # iterate over the data directories
        for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
            # check if IMAGE_DIRECTORY_ENTRY_SECURITY exists
            if d.name == 'IMAGE_DIRECTORY_ENTRY_SECURITY':
                if verbose == True:
                    logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
                # if data is present in the security directory
                if d.VirtualAddress > 0:
                    # get the size of the signature
                    size_in_sig = pe.get_word_from_offset(d.VirtualAddress)
                    # if the size of the signature is the same as the size of the data directory
                    if size_in_sig == d.Size:
                        if verbose == True:
                            logger_rew.info('find certificate')
                        # zero out the data
                        pe.set_bytes_at_offset(d.VirtualAddress, ('\x00'*(d.Size)).encode())
                        d.VirtualAddress = 0
                        d.Size = 0
                        
        # write the pe object to the output path
        pe.write(output_path)

        # verify action change
        pe = self.try_parse_pe(output_path)
        if pe:
            for d in pe.OPTIONAL_HEADER.DATA_DIRECTORY:
                if d.name == 'IMAGE_DIRECTORY_ENTRY_SECURITY':
                    if verbose == True:
                        logger_rew.info('%s\t%s\t%s' %(d.name, hex(d.VirtualAddress), hex(d.Size)))
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))
        
        # return the path of the new sample
        return output_path

class ArmCR(Arm):
    """The CR arm class, which randomizes code.

    Args:
        Arm (arm): The arm class
    """
    def __init__(self, idx):
        """init function for CR arm

        Args:
            idx (int): Index of the arm
        """
        super().__init__(idx)
        self.action = 'CR'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the CR arm to a sample. Requires a CR file in the randomizer folder to work

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): Path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # get the path of the CR file in the random folder
        cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(output_path) + '.CR'
        # check if randomized file exists
        if os.path.exists(cr_path) == True:
            os.system('cp -p %s %s' %(cr_path, output_path))
            if verbose == True:
                logger_rew.info('have CR file')
        else:
            if verbose == True:
                logger_rew.info('do not have CR file')
            os.system('cp -p %s %s' %(input_path, output_path))

        # verify action change
        pe = self.try_parse_pe(output_path)
        if pe == None:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))
        
        # return the path of the new sample
        return output_path

class ArmBC(Arm):
    """The BC arm class, which breaks the optional header checksum of a file

    Args:
        Arm (arm): The arm class
    """
    def __init__(self, idx):
        """init function for BC arm

        Args:
            idx (int): Index of the arm
        """
        super().__init__(idx)
        self.action = 'BC'
        self.description = self.action

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the BC arm to a sample

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): Path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # create pe object
        pe = pefile.PE(input_path)
        # get the original checksum
        checksum_before = pe.OPTIONAL_HEADER.CheckSum
        # set the checksum to 0
        pe.OPTIONAL_HEADER.CheckSum = 0
        pe.write(output_path)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            checksum_after = pe.OPTIONAL_HEADER.CheckSum
            if verbose == True:
                logger_rew.info('CheckSum: before %s, after %s' %(hex(checksum_before), hex(checksum_after)))
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))


        return output_path

class ArmSP(Arm):
    """The SP arm class, which appends data to a section of a PE file

    Args:
        Arm (arm): The arm class
    """
    def __init__(self, idx, section_idx=None, content=None):
        """function to init the SP arm

        Args:
            idx (int): Index of the arm
            section_idx (int, optional): Index of the section. Defaults to None.
            content (bin, optional): Content to append. Defaults to None.
        """
        super().__init__(idx)
        # check if content is given and only one byte
        if content and len(content) == 1:
            self.action = 'SP1'
        # else set action to SP/SP+Rand
        else:
            self.action = 'SP'
        self.section_idx = section_idx
        self.content = content
        self.update_description()

    def update_description(self):
        """function to update the description of the arm
        """
        # no content given -> set description to SP+Rand
        if self.content == None:
            self.description = 'SP+Rand'
        # content given and only one byte -> set description to SP+1
        elif len(self.content) == 1:
            self.description = 'SP+1'
        # content given -> set description to SP+hash(content)
        else:
            self.description = 'SP+' + hashlib.md5(self.content).hexdigest()[:8]

    def set_content(self, content):
        """function to set the content of the arm

        Args:
            content (bin): Content to append
        """
        self.content = content
        # if content is only one byte, set action to SP1
        if len(content) == 1:
            self.action = 'SP1'
        self.update_description()

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the SP arm to a sample

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): Path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # create pe object
        pe = pefile.PE(input_path)

        # find out all available_sections
        dict_idx_to_available_size = {}
        for idx, section in enumerate(pe.sections):
            # get the available size in the section
            available_size = self.get_available_size_safe(pe, idx)
            # if there is space in the section, add to dict
            if available_size > 0:
                dict_idx_to_available_size[idx] = available_size
        # if there is no space in any section, return the original file
        if len(dict_idx_to_available_size) == 0:
            if verbose == True:
                logger_rew.info('no section has free space, return the original sample')
            os.system('cp -p %s %s' %(input_path, output_path))

            return output_path
        # get the section index
        append_section_idx = self.section_idx
        # arm first use, or cannot be directly applied
        if append_section_idx == None or append_section_idx not in dict_idx_to_available_size.keys():
            append_section_idx = random.choice(list(dict_idx_to_available_size.keys()))
        # get the available size
        available_size = dict_idx_to_available_size[append_section_idx]

        # arm first use, save for later use 
        if self.section_idx == None:
            self.section_idx = append_section_idx
        if self.content == None:
            _, _, self.content = Utils.get_random_content()

        append_content = self.content
        # if it's SP1, do not need to extend content
        if len(append_content) != 1:   
            # extend content to fit available size         
            while available_size > len(append_content):   
                append_content += self.content                    
            append_content = bytes(append_content[:available_size])
        # write content to the section
        target_section = pe.sections[append_section_idx]
        pe.set_bytes_at_offset(target_section.PointerToRawData + target_section.Misc_VirtualSize, append_content)
        if verbose == True:
            logger_rew.info('section_idx: %d, content lenth: %d' %(append_section_idx, len(append_content)))
        pe.write(output_path)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe == None:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))

        # return the path of the new sample
        return output_path

class ArmCP1(Arm):  
    """The CP1 arm class, which adds one byte to the code section of a PE file

    Args:
        Arm (arm): The arm class
    """
    def __init__(self, idx):
        """init function for CP1 arm

        Args:
            idx (int): Index of the arm
        """
        super().__init__(idx)
         # special case, only CP1 init with section_idx, SP1 only set_content
        self.action = 'CP1'    
        self.description = 'CP+1'

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the CP1 arm to a sample

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): Path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # create pe object
        pe = pefile.PE(input_path)
        code_section_idx = None
        # iterate over the sections
        for section_idx, section in enumerate(pe.sections):

            try:
                # if the section is a code section
                if section.Name[:5].decode('utf-8') == '.text':
                    # get the available size in the section
                    available_size = self.get_available_size_safe(pe, section_idx)
                    # if there is space in the section, set the code_section_idx
                    if available_size > 0:
                        code_section_idx = section_idx
                    # if there is no space, return the original file
                    else:
                        if verbose == True:
                            logger_rew.info('code section has free space')
                    break
            except Exception as e:
               logger_rew.error('decode section name fail')
        # if there is a code section
        if code_section_idx != None:
            # set the targe tsection
            target_section = pe.sections[code_section_idx]
            # write one byte to the section
            pe.set_bytes_at_offset(target_section.PointerToRawData + target_section.Misc_VirtualSize, bytes([1]))
            pe.write(output_path)
    
            # verify action changes
            pe = self.try_parse_pe(output_path)
            if pe == None:
                if verbose == True:
                    logger_rew.info('pefile cannot parse, restore original file')
                os.system('cp -p %s %s' %(input_path, output_path))
        else:

            os.system('cp -p %s %s' %(input_path, output_path))

        # return the path of the new sample
        return output_path

class ArmSR(Arm):
    """The SR arm class, which changes the name of a section in a PE file

    Args:
        Arm (_type_): _description_
    """
    def __init__(self, idx, mutate_one_byte=None):
        """init function for SR arm

        Args:
            idx (int): index of the arm
            mutate_one_byte (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(idx)
        self.mutate_one_byte = mutate_one_byte
        self.action = 'SR'
        self.section_idx = None
        self.new_name = None
        self.old_name = None
        self.update_description()

    def update_description(self):
        """function to update the description of the arm
        """
        # if mutate_one_byte is set, set description to SR+1
        if self.mutate_one_byte:
            self.action = 'SR1'
            self.description = 'SR+1'
        # if new_name is None, set description to SR+Rand
        elif self.new_name == None:
            self.description = 'SR+Rand'
        # else set description to SR+hash(new_name)
        else:
            self.description = 'SR+' + hashlib.md5((str(self.section_idx) + self.new_name).encode()).hexdigest()[:8]

    def randomly_change_one_byte(self, old_name):
        """function to randomly change one byte of a string

        Args:
            old_name (String): old section name

        Returns:
            String: new section name
        """
        # if the old name is empty, return a random letter
        if len(old_name) == 0:
            return random.choice(string.ascii_lowercase)
        new_name = old_name
        new_name_list = list(old_name)
        # randomly change one byte
        while(new_name == old_name):
            name_idx = random.randint(0, len(list(old_name))-1)
            new_name_list[name_idx] = random.choice(string.ascii_lowercase)
            new_name = ''.join(new_name_list)
        return new_name

    def mutate_section_name_one_byte(self):
        """function to mutate the section name by one byte
        """
        self.new_name = self.randomly_change_one_byte(self.old_name)
        self.action = 'SR1'
        self.description = 'SR+1'

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the SR arm to a sample

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): Path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # create pe object
        pe = pefile.PE(input_path)
        # get the section names
        list_section_name = self.get_section_name_list(pe)
        # if there are no section names, return the original file
        if len(list_section_name) == 0:
            os.system('cp -p %s %s' %(input_path, output_path))
            return output_path

        if verbose == True:
            self.print_section_names(pe)
        # if mutate_one_byte is set, mutate the section name by one byte
        if self.new_name == None and self.old_name == None and self.section_idx == None:
            # arm first use
            section_idx = random.choice(range(len(list_section_name)))
            old_name = list_section_name[section_idx]
            if self.description == 'SR+1':    # if SR1, change one byte
                new_name = self.randomly_change_one_byte(old_name)
            else:                       # if SR, randomly_select_new_name
                new_name = old_name
                while new_name == old_name:
                    new_name, _, _ = Utils.get_random_content()
            if verbose == True:
                logger_rew.info('old_name: %s, new_name: %s' %(old_name, new_name))

            # save for reuse later is succ
            self.new_name = new_name
            self.section_idx = section_idx
            self.old_name = old_name
        else:
            # reuse succ arm
            new_name = self.new_name
            if self.old_name in list_section_name:
                section_idx = list_section_name.index(self.old_name)
            elif self.section_idx >= len(list_section_name):
                section_idx = random.choice(range(len(list_section_name)))
            else:
                section_idx = self.section_idx

        pe.sections[section_idx].Name = new_name.encode()
        pe.write(output_path)

        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            if verbose == True:
                self.print_section_names(pe)
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))


        return output_path

class ArmSA(Arm):
    """The SA arm class, which adds a new section to a PE file

    Args:
        Arm (_type_): _description_
    """
    def __init__(self, idx, content=None):
        """init function for SA arm

        Args:
            idx (int): index of the arm
            content (bin, optional): Content to add as a new section. Defaults to None.
        """
        super().__init__(idx)
        self.content = content
        if content and len(content) == 1:
            self.action = 'SA1'
        else:
            self.action = 'SA'
        self.section_name = None

        self.description = None
        self.update_description()
    
    def set_content(self, content):
        """function to set the content of the arm

        Args:
            content (bin): Content to set
        """
        self.content = content
        if len(content) == 1:
            self.action = 'SA1'
        self.update_description()

    def update_description(self):
        """function to update the description of the arm
        """
        # if content is None, set description to SA+Rand
        if self.content == None:
            self.description = 'SA+Rand'
        # if content is only one byte, set description to SA+1
        elif len(self.content) == 1:
            self.description = 'SA+1'
        # else set description to SA+hash(content)
        else:
            self.description = 'SA+' + hashlib.md5(self.content).hexdigest()[:8]

    def transfer(self, input_path, output_folder=rewriter_output_folder, verbose=True):
        """function to apply the SA arm to a sample

        Args:
            input_path (path): Path to the input sample
            output_folder (path, optional): Path to where to write the sample to. Defaults to rewriter_output_folder.
            verbose (bool, optional): Verbose output. Defaults to True.

        Returns:
            path: Path the new sample is written to
        """
        if verbose == True:
            logger_rew.info('=== %s ===' %self.action)
        # get the output path
        output_path = self.get_output_path(output_folder, input_path)
        # create pe object
        pe = pefile.PE(input_path)
        if verbose == True:
            self.print_section_names(pe)
        # if content is None, generate random content
        if self.content == None:
            # SA first use
            self.section_name, _, self.content = Utils.get_random_content()
        # if content is only one byte, set action to SA1
        if self.section_name == None:
            # SA1 first use
            self.section_name, _, _ = Utils.get_random_content()
        # get the numer of sections 
        number_of_section = pe.FILE_HEADER.NumberOfSections
        # get the last section
        last_section = number_of_section - 1
        # get the file alignment and section alignment
        file_alignment = pe.OPTIONAL_HEADER.FileAlignment
        section_alignment = pe.OPTIONAL_HEADER.SectionAlignment
        # if the last section is greater or equal to the number of sections, return the original file
        if last_section >= len(pe.sections):
            os.system('cp -p %s %s' %(input_path, output_path))
            return output_path
        
        # get the new section header offset
        new_section_header_offset = (pe.sections[number_of_section - 1].get_file_offset() + 40)
        # get the space before the first section
        next_header_space_content_sum = pe.get_qword_from_offset(new_section_header_offset) + \
                pe.get_qword_from_offset(new_section_header_offset + 8) + \
                pe.get_qword_from_offset(new_section_header_offset + 16) + \
                pe.get_qword_from_offset(new_section_header_offset + 24) + \
                pe.get_qword_from_offset(new_section_header_offset + 32)
        first_section_offset = pe.sections[0].PointerToRawData
        next_header_space_size = first_section_offset - new_section_header_offset
        # if there is no space before the first section, return the original file
        if next_header_space_size < 40:
            if verbose == True:
                logger_rew.info('no free space to add a new header before the fist section')
            os.system('cp -p %s %s' %(input_path, output_path))
            return output_path
        # if there is hidden header or data, return the original file
        if next_header_space_content_sum != 0:
            if verbose == True:
                logger_rew.info('exist hidden header or data, such as VB header')
            os.system('cp -p %s %s' %(input_path, output_path))

            return output_path
        # get the file size, raw size, virtual size, raw offset, virtual offset and characteristics
        file_size = os.path.getsize(input_path)
        raw_size = self.align(len(self.content), file_alignment)
        virtual_size = self.align(len(self.content), section_alignment)
        raw_offset = file_size

    
        # Resize the PE file
        os.system('cp -p %s %s' %(input_path, output_path))
        pe = pefile.PE(output_path)
        original_size = os.path.getsize(output_path)
        fd = open(output_path, 'a+b')
        map = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_WRITE)
        map.resize(original_size + raw_size)
        map.close()
        fd.close()
        # Reopen the PE file
        pe = pefile.PE(output_path)
        # get the last section
        virtual_offset = self.align((pe.sections[last_section].VirtualAddress +
                            pe.sections[last_section].Misc_VirtualSize),
                            section_alignment)
        characteristics = 0xE0000020
        self.section_name = self.section_name + ('\x00' * (8-len(self.section_name)))
    
        # Add the New Section Header
        hex(pe.get_qword_from_offset(new_section_header_offset))
        pe.set_bytes_at_offset(new_section_header_offset, self.section_name.encode())
        pe.set_dword_at_offset(new_section_header_offset + 8, virtual_size)
        pe.set_dword_at_offset(new_section_header_offset + 12, virtual_offset)
        pe.set_dword_at_offset(new_section_header_offset + 16, raw_size)
        pe.set_dword_at_offset(new_section_header_offset + 20, raw_offset)
        pe.set_bytes_at_offset(new_section_header_offset + 24, (12 * '\x00').encode())
        pe.set_dword_at_offset(new_section_header_offset + 36, characteristics)
        pe.FILE_HEADER.NumberOfSections += 1
        pe.OPTIONAL_HEADER.SizeOfImage = virtual_size + virtual_offset
        pe.set_bytes_at_offset(raw_offset, self.content)
        
        # try to write the pe object
        try:
            pe.write(output_path)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger_rew.error('%s %s:%s pe.write fail' %(exc_type, fname, exc_tb.tb_lineno))
            os.system('cp -p %s %s' %(input_path, output_path))
        
        # verify action changes
        pe = self.try_parse_pe(output_path)
        if pe:
            if verbose == True:
                self.print_section_names(pe)
                logger_rew.info('new section len: %d' %len(self.content))
        else:
            if verbose == True:
                logger_rew.info('pefile cannot parse, restore original file')
            os.system('cp -p %s %s' %(input_path, output_path))
        
        return output_path
