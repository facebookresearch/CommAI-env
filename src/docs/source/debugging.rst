Debugging
=========

A useful tool for debugging is to log what it has been going on. You can log
anything from your tasks by:

#. Add import logging to the top of the file
#. Create your logger by doing (possibly inside the __init__ method)
    `self.logger = logging.getLogger(__name__)`. Strictly speaking you could send
    any string to the getLogger function, which stands for the name of your logger,
    but in this way you just send the name of your working file name, which is
    clean and save you from thinking of a name.

#. Whenever you need to log something within your task you can do:

    * self.logger.debug("spam, spam, spam, eggs, bacon and spam") to log at the DEBUG level
    * self.logger.info("spam, spam, spam, eggs, bacon and spam") to log at the INFO level
    * self.logger.warn("spam, spam, spam, eggs, bacon and spam") to log at the WARNING level
    * self.logger.error("spam, spam, spam, eggs, bacon and spam") to log at the ERROR level

    The outputs of the loggers are saved to the files errors.log
    (only messages at the ERROR level), info.log (messages with INFO, WARNING and
    ERROR level) and debug.log (all messages).
