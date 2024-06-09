import chainlit as cl
from langchain.chains import LLMChain
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

llm = Ollama(model="mayflowergmbh/occiglot-7b-fr-en-instruct")
template = """Question: {question}"""


@cl.on_chat_start
def main():
    # Instantiate the chain for that user session
    prompt = PromptTemplate(template=template, input_variables=["question"])
    llm_chain = LLMChain(prompt=prompt, llm=llm, verbose=True)

    # Store the chain in the user session
    cl.user_session.set("llm_chain", llm_chain)


@cl.on_message
async def main(message: cl.Message):
    # Retrieve the chain from the user session
    llm_chain = cl.user_session.get("llm_chain")  # type: LLMChain

    await cl.Message(content=f"I received this : '{message.content}'").send()

    # Call the chain asynchronously
    res = await llm_chain.acall(
        message.content, callbacks=[cl.AsyncLangchainCallbackHandler()]
    )

    # Do any post-processing here

    # Send the response
    await cl.Message(content=res["text"]).send()
